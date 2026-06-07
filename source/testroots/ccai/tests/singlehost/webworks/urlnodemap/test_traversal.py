"""
    Tests for tree traversal methods on URLNode and URLNodeMap.

    This module contains unit tests for the ancestors(), descendants(),
    iterate_nodes(), and iterate_leaves() traversal methods.
"""

from ccai.webworks.urlnodemap.urlnode import URLNode
from ccai.webworks.urlnodemap.urlnodemap import URLNodeMap


# =============================================================================
# Unit Tests for URLNode.ancestors()
# =============================================================================

def test_urlnode_ancestors_root_yields_nothing():
    """
        Test that calling ancestors() on the root node yields no nodes.
    """
    root = URLNode(segment="", path="/", parent=None)

    ancestors = list(root.ancestors())

    if len(ancestors) != 0:
        errmsg = f"Expected 0 ancestors for root, got {len(ancestors)}"
        raise AssertionError(errmsg)

    return


def test_urlnode_ancestors_single_level():
    """
        Test that a child of root yields only the root as ancestor.
    """
    root = URLNode(segment="", path="/", parent=None)
    child = root.add_child("api")

    ancestors = list(child.ancestors())

    if len(ancestors) != 1:
        errmsg = f"Expected 1 ancestor, got {len(ancestors)}"
        raise AssertionError(errmsg)

    if ancestors[0] is not root:
        errmsg = "Expected ancestor to be the root node"
        raise AssertionError(errmsg)

    return


def test_urlnode_ancestors_multi_level():
    """
        Test that ancestors() yields nodes from parent to root for a deep node.
    """
    root = URLNode(segment="", path="/", parent=None)
    api = root.add_child("api")
    v1 = api.add_child("v1")
    users = v1.add_child("users")

    ancestors = list(users.ancestors())

    if len(ancestors) != 3:
        errmsg = f"Expected 3 ancestors, got {len(ancestors)}"
        raise AssertionError(errmsg)

    if ancestors[0] is not v1:
        errmsg = f"Expected first ancestor to be v1 node, got path '{ancestors[0].path}'"
        raise AssertionError(errmsg)

    if ancestors[1] is not api:
        errmsg = f"Expected second ancestor to be api node, got path '{ancestors[1].path}'"
        raise AssertionError(errmsg)

    if ancestors[2] is not root:
        errmsg = f"Expected third ancestor to be root node, got path '{ancestors[2].path}'"
        raise AssertionError(errmsg)

    return


def test_urlnode_ancestors_last_is_root():
    """
        Test that the last ancestor yielded is always the root node.
    """
    node_map = URLNodeMap()
    deep_node = node_map.get_or_create_node("/a/b/c/d/e")

    ancestors = list(deep_node.ancestors())

    last_ancestor = ancestors[-1]
    if last_ancestor.path != "/":
        errmsg = f"Expected last ancestor to be root ('/'), got '{last_ancestor.path}'"
        raise AssertionError(errmsg)

    return


# =============================================================================
# Unit Tests for URLNode.descendants()
# =============================================================================

def test_urlnode_descendants_leaf_yields_nothing():
    """
        Test that calling descendants() on a leaf node yields no nodes.
    """
    root = URLNode(segment="", path="/", parent=None)
    leaf = root.add_child("leaf")

    descendants = list(leaf.descendants())

    if len(descendants) != 0:
        errmsg = f"Expected 0 descendants for leaf, got {len(descendants)}"
        raise AssertionError(errmsg)

    return


def test_urlnode_descendants_single_child():
    """
        Test that descendants() yields a single child.
    """
    root = URLNode(segment="", path="/", parent=None)
    child = root.add_child("api")

    descendants = list(root.descendants())

    if len(descendants) != 1:
        errmsg = f"Expected 1 descendant, got {len(descendants)}"
        raise AssertionError(errmsg)

    if descendants[0] is not child:
        errmsg = "Expected descendant to be the child node"
        raise AssertionError(errmsg)

    return


def test_urlnode_descendants_depth_first_order():
    """
        Test that descendants() yields nodes in depth-first order.
    """
    root = URLNode(segment="", path="/", parent=None)
    api = root.add_child("api")
    v1 = api.add_child("v1")
    users = v1.add_child("users")
    docs = root.add_child("docs")

    descendants = list(root.descendants())

    if len(descendants) != 4:
        errmsg = f"Expected 4 descendants, got {len(descendants)}"
        raise AssertionError(errmsg)

    # Depth-first: api -> v1 -> users -> docs
    expected_paths = ["/api", "/api/v1", "/api/v1/users", "/docs"]
    actual_paths = [n.path for n in descendants]

    if actual_paths != expected_paths:
        errmsg = f"Expected depth-first order {expected_paths}, got {actual_paths}"
        raise AssertionError(errmsg)

    return


def test_urlnode_descendants_wide_tree():
    """
        Test that descendants() covers all children in a wide tree.
    """
    root = URLNode(segment="", path="/", parent=None)
    a = root.add_child("a")
    b = root.add_child("b")
    c = root.add_child("c")

    descendants = list(root.descendants())

    if len(descendants) != 3:
        errmsg = f"Expected 3 descendants, got {len(descendants)}"
        raise AssertionError(errmsg)

    descendant_segments = {n.segment for n in descendants}
    expected_segments = {"a", "b", "c"}

    if descendant_segments != expected_segments:
        errmsg = f"Expected segments {expected_segments}, got {descendant_segments}"
        raise AssertionError(errmsg)

    return


# =============================================================================
# Unit Tests for URLNodeMap.iterate_nodes()
# =============================================================================

def test_urlnodemap_iterate_nodes_empty_tree():
    """
        Test that iterate_nodes() on an empty tree yields only the root.
    """
    node_map = URLNodeMap()

    nodes = list(node_map.iterate_nodes())

    if len(nodes) != 1:
        errmsg = f"Expected 1 node (root), got {len(nodes)}"
        raise AssertionError(errmsg)

    if nodes[0].path != "/":
        errmsg = f"Expected root node, got path '{nodes[0].path}'"
        raise AssertionError(errmsg)

    return


def test_urlnodemap_iterate_nodes_includes_all():
    """
        Test that iterate_nodes() yields every node in the tree.
    """
    node_map = URLNodeMap()
    node_map.get_or_create_node("/api/v1/users")
    node_map.get_or_create_node("/docs")

    nodes = list(node_map.iterate_nodes())

    # root + api + v1 + users + docs = 5
    if len(nodes) != 5:
        errmsg = f"Expected 5 nodes, got {len(nodes)}"
        raise AssertionError(errmsg)

    paths = {n.path for n in nodes}
    expected_paths = {"/", "/api", "/api/v1", "/api/v1/users", "/docs"}

    if paths != expected_paths:
        errmsg = f"Expected paths {expected_paths}, got {paths}"
        raise AssertionError(errmsg)

    return


def test_urlnodemap_iterate_nodes_depth_first():
    """
        Test that iterate_nodes() yields nodes in depth-first order.
    """
    node_map = URLNodeMap()
    node_map.get_or_create_node("/api/v1")
    node_map.get_or_create_node("/docs")

    nodes = list(node_map.iterate_nodes())

    expected_paths = ["/", "/api", "/api/v1", "/docs"]
    actual_paths = [n.path for n in nodes]

    if actual_paths != expected_paths:
        errmsg = f"Expected depth-first order {expected_paths}, got {actual_paths}"
        raise AssertionError(errmsg)

    return


def test_urlnodemap_iterate_nodes_each_node_once():
    """
        Test that iterate_nodes() yields each node exactly once.
    """
    node_map = URLNodeMap()
    node_map.get_or_create_node("/a/b")
    node_map.get_or_create_node("/a/c")
    node_map.get_or_create_node("/d")

    nodes = list(node_map.iterate_nodes())
    paths = [n.path for n in nodes]

    if len(paths) != len(set(paths)):
        errmsg = f"Duplicate nodes found in iteration: {paths}"
        raise AssertionError(errmsg)

    return


# =============================================================================
# Unit Tests for URLNodeMap.iterate_leaves()
# =============================================================================

def test_urlnodemap_iterate_leaves_empty_tree():
    """
        Test that iterate_leaves() yields nothing on a tree with no handlers.
    """
    node_map = URLNodeMap()
    node_map.get_or_create_node("/api/v1/users")

    leaves = list(node_map.iterate_leaves())

    if len(leaves) != 0:
        errmsg = f"Expected 0 leaves, got {len(leaves)}"
        raise AssertionError(errmsg)

    return


def test_urlnodemap_iterate_leaves_single_handler():
    """
        Test that iterate_leaves() yields a node with a handler.
    """
    node_map = URLNodeMap()
    users = node_map.get_or_create_node("/api/v1/users")
    users.attach_handler("GET", lambda: "users list")

    leaves = list(node_map.iterate_leaves())

    if len(leaves) != 1:
        errmsg = f"Expected 1 leaf, got {len(leaves)}"
        raise AssertionError(errmsg)

    if leaves[0].path != "/api/v1/users":
        errmsg = f"Expected leaf at '/api/v1/users', got '{leaves[0].path}'"
        raise AssertionError(errmsg)

    return


def test_urlnodemap_iterate_leaves_multiple_handlers():
    """
        Test that iterate_leaves() yields all nodes with handlers.
    """
    node_map = URLNodeMap()
    users = node_map.get_or_create_node("/api/v1/users")
    users.attach_handler("GET", lambda: "users list")

    docs = node_map.get_or_create_node("/docs")
    docs.attach_handler("GET", lambda: "docs page")

    leaves = list(node_map.iterate_leaves())

    if len(leaves) != 2:
        errmsg = f"Expected 2 leaves, got {len(leaves)}"
        raise AssertionError(errmsg)

    leaf_paths = {n.path for n in leaves}
    expected_paths = {"/api/v1/users", "/docs"}

    if leaf_paths != expected_paths:
        errmsg = f"Expected leaf paths {expected_paths}, got {leaf_paths}"
        raise AssertionError(errmsg)

    return


def test_urlnodemap_iterate_leaves_skips_intermediate():
    """
        Test that iterate_leaves() skips intermediate nodes without handlers.
    """
    node_map = URLNodeMap()
    node_map.get_or_create_node("/api/v1/users")
    users = node_map.get_node("/api/v1/users")
    users.attach_handler("GET", lambda: "users")

    # /api and /api/v1 are intermediate nodes without handlers
    leaves = list(node_map.iterate_leaves())

    if len(leaves) != 1:
        errmsg = f"Expected 1 leaf, got {len(leaves)}"
        raise AssertionError(errmsg)

    if leaves[0].path != "/api/v1/users":
        errmsg = f"Expected leaf at '/api/v1/users', got '{leaves[0].path}'"
        raise AssertionError(errmsg)

    return


def test_urlnodemap_iterate_leaves_handler_on_intermediate():
    """
        Test that iterate_leaves() includes intermediate nodes that have handlers.
    """
    node_map = URLNodeMap()
    api = node_map.get_or_create_node("/api")
    api.attach_handler("GET", lambda: "api root")

    users = node_map.get_or_create_node("/api/v1/users")
    users.attach_handler("GET", lambda: "users")

    leaves = list(node_map.iterate_leaves())

    if len(leaves) != 2:
        errmsg = f"Expected 2 leaves, got {len(leaves)}"
        raise AssertionError(errmsg)

    leaf_paths = {n.path for n in leaves}
    expected_paths = {"/api", "/api/v1/users"}

    if leaf_paths != expected_paths:
        errmsg = f"Expected leaf paths {expected_paths}, got {leaf_paths}"
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


def _collect_all_nodes_dfs(root):
    """
        Collect all nodes in the tree using a manual depth-first traversal.

        :param root: The root URLNode.
        :returns: A list of all URLNode instances.
    """
    nodes = [root]
    for child in root.children.values():
        nodes.extend(_collect_all_nodes_dfs(child))
    return nodes


# =============================================================================
# Property-Based Tests
# =============================================================================

# Feature: url-node-map, Property 8: Traversal Completeness
# *For any* URL Node Map, `iterate_nodes()` SHALL yield every node in the
# tree exactly once, and `iterate_leaves()` SHALL yield exactly those nodes
# where `is_leaf` is True.
# **Validates: Requirements 5.1, 5.2**


def test_property_8_traversal_completeness_iterate_nodes_yields_all():
    """
        Property 8: Traversal Completeness - iterate_nodes yields every node

        For any URL Node Map populated with random paths, iterate_nodes()
        SHALL yield every node in the tree exactly once. The set of paths
        from iterate_nodes must equal the set of paths from a manual
        depth-first collection.

        **Validates: Requirements 5.1, 5.2**
    """
    for iteration in range(100):
        random.seed(iteration * 11111)

        node_map = URLNodeMap()

        # Generate and insert random paths
        num_paths = random.randint(1, 15)
        paths = _generate_distinct_paths(num_paths, min_segments=1, max_segments=4)
        for path in paths:
            node_map.get_or_create_node(path)

        # Attach handlers to a random subset to create leaves
        all_created = list(node_map.iterate_nodes())
        handler_count = random.randint(0, len(all_created))
        handler_indices = random.sample(range(len(all_created)), handler_count)
        for idx in handler_indices:
            node = all_created[idx]
            if not node.is_leaf:
                node.attach_handler("GET", lambda: None)

        # Collect nodes via iterate_nodes
        iterated_nodes = list(node_map.iterate_nodes())
        iterated_paths = [n.path for n in iterated_nodes]

        # Collect nodes via manual DFS
        manual_nodes = _collect_all_nodes_dfs(node_map.root)
        manual_paths = [n.path for n in manual_nodes]

        # Check same set of paths
        if set(iterated_paths) != set(manual_paths):
            missing = set(manual_paths) - set(iterated_paths)
            extra = set(iterated_paths) - set(manual_paths)
            errmsg = (
                f"Iteration {iteration}: iterate_nodes() path set mismatch.\n"
                f"  Missing: {missing}\n"
                f"  Extra: {extra}\n"
                f"  Inserted paths: {paths}"
            )
            raise AssertionError(errmsg)

        # Check no duplicates (each node exactly once)
        if len(iterated_paths) != len(set(iterated_paths)):
            duplicates = [p for p in iterated_paths if iterated_paths.count(p) > 1]
            errmsg = (
                f"Iteration {iteration}: iterate_nodes() yielded duplicates.\n"
                f"  Duplicates: {set(duplicates)}"
            )
            raise AssertionError(errmsg)

    return


def test_property_8_traversal_completeness_iterate_leaves_matches_is_leaf():
    """
        Property 8: Traversal Completeness - iterate_leaves matches is_leaf

        For any URL Node Map, iterate_leaves() SHALL yield exactly those
        nodes where is_leaf is True. No non-leaf node shall appear, and
        no leaf node shall be missing.

        **Validates: Requirements 5.1, 5.2**
    """
    for iteration in range(100):
        random.seed(iteration * 22222)

        node_map = URLNodeMap()

        # Generate and insert random paths
        num_paths = random.randint(1, 12)
        paths = _generate_distinct_paths(num_paths, min_segments=1, max_segments=4)
        for path in paths:
            node_map.get_or_create_node(path)

        # Attach handlers to a random subset of nodes
        all_nodes = list(node_map.iterate_nodes())
        num_handlers = random.randint(0, len(all_nodes))
        handler_indices = random.sample(range(len(all_nodes)), num_handlers)
        for idx in handler_indices:
            node = all_nodes[idx]
            if not node.is_leaf:
                node.attach_handler("GET", lambda: None)

        # Collect leaves via iterate_leaves
        iterated_leaves = list(node_map.iterate_leaves())
        iterated_leaf_paths = {n.path for n in iterated_leaves}

        # Collect expected leaves via manual check of is_leaf on all nodes
        expected_leaf_paths = set()
        for node in node_map.iterate_nodes():
            if node.is_leaf:
                expected_leaf_paths.add(node.path)

        if iterated_leaf_paths != expected_leaf_paths:
            missing = expected_leaf_paths - iterated_leaf_paths
            extra = iterated_leaf_paths - expected_leaf_paths
            errmsg = (
                f"Iteration {iteration}: iterate_leaves() mismatch.\n"
                f"  Missing leaves: {missing}\n"
                f"  Extra non-leaves: {extra}\n"
                f"  Inserted paths: {paths}"
            )
            raise AssertionError(errmsg)

        # Check no duplicates in leaves
        leaf_paths_list = [n.path for n in iterated_leaves]
        if len(leaf_paths_list) != len(set(leaf_paths_list)):
            duplicates = [p for p in leaf_paths_list if leaf_paths_list.count(p) > 1]
            errmsg = (
                f"Iteration {iteration}: iterate_leaves() yielded duplicates.\n"
                f"  Duplicates: {set(duplicates)}"
            )
            raise AssertionError(errmsg)

    return


# =============================================================================
# Property 12: Ancestor Chain Integrity
# =============================================================================

# Feature: url-node-map, Property 12: Ancestor Chain Integrity
# *For any* node, iterating `ancestors()` SHALL yield nodes in order from
# parent to root, and the final node SHALL be the root node with path "/".
# **Validates: Requirements 5.5**


def test_property_12_ancestor_chain_integrity_order_and_root():
    """
        Property 12: Ancestor Chain Integrity

        For any non-root node in a randomly generated URL Node Map,
        iterating ancestors() SHALL yield nodes in order from parent
        to root, and the final node SHALL be the root node with path "/".

        **Validates: Requirements 5.5**
    """
    for iteration in range(100):
        random.seed(iteration * 44444)

        node_map = URLNodeMap()

        # Generate and insert random paths
        num_paths = random.randint(1, 10)
        paths = _generate_distinct_paths(num_paths, min_segments=1, max_segments=5)
        for path in paths:
            node_map.get_or_create_node(path)

        # Collect all non-root nodes
        all_nodes = list(node_map.iterate_nodes())
        non_root_nodes = [n for n in all_nodes if n.parent is not None]

        for node in non_root_nodes:
            ancestors = list(node.ancestors())

            # Must have at least one ancestor (the root)
            if len(ancestors) == 0:
                errmsg = (
                    f"Iteration {iteration}: Node at '{node.path}' has no "
                    f"ancestors but is not root."
                )
                raise AssertionError(errmsg)

            # First ancestor must be the immediate parent
            if ancestors[0] is not node.parent:
                errmsg = (
                    f"Iteration {iteration}: First ancestor of '{node.path}' "
                    f"should be parent '{node.parent.path}', got "
                    f"'{ancestors[0].path}'."
                )
                raise AssertionError(errmsg)

            # Each successive ancestor must be the parent of the previous
            for i in range(1, len(ancestors)):
                if ancestors[i] is not ancestors[i - 1].parent:
                    errmsg = (
                        f"Iteration {iteration}: Ancestor chain broken at "
                        f"index {i} for node '{node.path}'. "
                        f"Expected parent of '{ancestors[i - 1].path}' "
                        f"('{ancestors[i - 1].parent.path}'), got "
                        f"'{ancestors[i].path}'."
                    )
                    raise AssertionError(errmsg)

            # Last ancestor must be the root node with path "/"
            last_ancestor = ancestors[-1]
            if last_ancestor.path != "/":
                errmsg = (
                    f"Iteration {iteration}: Last ancestor of '{node.path}' "
                    f"should be root ('/'), got '{last_ancestor.path}'."
                )
                raise AssertionError(errmsg)

            if last_ancestor.parent is not None:
                errmsg = (
                    f"Iteration {iteration}: Last ancestor of '{node.path}' "
                    f"should have parent=None (root), but parent is "
                    f"'{last_ancestor.parent.path}'."
                )
                raise AssertionError(errmsg)

    return


def test_property_12_ancestor_chain_integrity_root_yields_nothing():
    """
        Property 12: Ancestor Chain Integrity - Root node variant

        For the root node, ancestors() SHALL yield no nodes.

        **Validates: Requirements 5.5**
    """
    for iteration in range(100):
        random.seed(iteration * 55555)

        node_map = URLNodeMap()

        # Populate with random paths so the tree is non-trivial
        num_paths = random.randint(0, 8)
        paths = _generate_distinct_paths(num_paths, min_segments=1, max_segments=4)
        for path in paths:
            node_map.get_or_create_node(path)

        # Root ancestors must always be empty
        root_ancestors = list(node_map.root.ancestors())

        if len(root_ancestors) != 0:
            errmsg = (
                f"Iteration {iteration}: Root node should have 0 ancestors, "
                f"got {len(root_ancestors)}."
            )
            raise AssertionError(errmsg)

    return
