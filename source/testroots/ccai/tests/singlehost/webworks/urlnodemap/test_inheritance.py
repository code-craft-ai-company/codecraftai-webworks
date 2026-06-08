"""
    Tests for URLNode metadata inheritance methods.

    Tests cover:
    - get_effective_metadata: inheritance resolution walking up the tree
    - get_effective_access_policy: AND-combination of access policies
    - get_effective_tags: union merge and replace_tags behavior
    - get_effective_rate_limit: most restrictive limit selection
"""

from ccai.webworks.urlnodemap.urlnode import URLNode


# ============================================================================
# get_effective_metadata tests
# ============================================================================

def test_effective_metadata_returns_own_value():
    """
        A node's own metadata value is returned when set.
    """
    root = URLNode(segment="", path="/", parent=None)
    root.set_metadata("version", "v1")

    result = root.get_effective_metadata("version")

    assert result == "v1", f"Expected 'v1', got {result!r}"


def test_effective_metadata_inherits_from_parent():
    """
        A child node inherits metadata from its parent when not set locally.
    """
    root = URLNode(segment="", path="/", parent=None)
    root.set_metadata("version", "v1")
    child = root.add_child("api")

    result = child.get_effective_metadata("version")

    assert result == "v1", f"Expected 'v1', got {result!r}"


def test_effective_metadata_child_overrides_parent():
    """
        A child's own value overrides the parent's value.
    """
    root = URLNode(segment="", path="/", parent=None)
    root.set_metadata("version", "v1")
    child = root.add_child("api")
    child.set_metadata("version", "v2")

    result = child.get_effective_metadata("version")

    assert result == "v2", f"Expected 'v2', got {result!r}"



def test_effective_metadata_inherits_from_grandparent():
    """
        A grandchild inherits metadata from the grandparent when neither
        the child nor the grandchild set the value.
    """
    root = URLNode(segment="", path="/", parent=None)
    root.set_metadata("version", "v1")
    child = root.add_child("api")
    grandchild = child.add_child("users")

    result = grandchild.get_effective_metadata("version")

    assert result == "v1", f"Expected 'v1', got {result!r}"


def test_effective_metadata_nearest_ancestor_wins():
    """
        The nearest ancestor's value is returned, not the root's.
    """
    root = URLNode(segment="", path="/", parent=None)
    root.set_metadata("version", "v1")
    child = root.add_child("api")
    child.set_metadata("version", "v2")
    grandchild = child.add_child("users")

    result = grandchild.get_effective_metadata("version")

    assert result == "v2", f"Expected 'v2', got {result!r}"


def test_effective_metadata_returns_none_when_not_set():
    """
        Returns None when no node in the chain defines the key.
    """
    root = URLNode(segment="", path="/", parent=None)
    child = root.add_child("api")

    result = child.get_effective_metadata("version")

    assert result is None, f"Expected None, got {result!r}"


def test_effective_metadata_root_node_returns_own_or_none():
    """
        Root node returns its own value or None (no parent to inherit from).
    """
    root = URLNode(segment="", path="/", parent=None)

    result = root.get_effective_metadata("missing_key")

    assert result is None, f"Expected None, got {result!r}"


# ============================================================================
# get_effective_access_policy tests
# ============================================================================

def test_effective_access_policy_returns_none_when_not_set():
    """
        Returns None when no access policy is set in the chain.
    """
    root = URLNode(segment="", path="/", parent=None)
    child = root.add_child("api")

    result = child.get_effective_access_policy()

    assert result is None, f"Expected None, got {result!r}"


def test_effective_access_policy_returns_single_policy():
    """
        Returns the single policy when only one node defines it.
    """
    root = URLNode(segment="", path="/", parent=None)
    root.set_metadata("access_policy", "admin")
    child = root.add_child("api")

    result = child.get_effective_access_policy()

    assert result == "admin", f"Expected 'admin', got {result!r}"


def test_effective_access_policy_combines_multiple_policies():
    """
        Combines multiple policies via logical AND (returns list).
    """
    root = URLNode(segment="", path="/", parent=None)
    root.set_metadata("access_policy", "authenticated")
    child = root.add_child("admin")
    child.set_metadata("access_policy", "admin_role")

    result = child.get_effective_access_policy()

    # Child policy first, then parent (walking up the tree)
    assert isinstance(result, list), f"Expected list, got {type(result)}"
    assert "authenticated" in result, "Expected 'authenticated' in combined policies"
    assert "admin_role" in result, "Expected 'admin_role' in combined policies"
    assert len(result) == 2, f"Expected 2 policies, got {len(result)}"


def test_effective_access_policy_own_only():
    """
        Returns own policy directly when no parent has a policy.
    """
    root = URLNode(segment="", path="/", parent=None)
    child = root.add_child("api")
    child.set_metadata("access_policy", "public")

    result = child.get_effective_access_policy()

    assert result == "public", f"Expected 'public', got {result!r}"


def test_effective_access_policy_three_level_chain():
    """
        Combines policies from three levels.
    """
    root = URLNode(segment="", path="/", parent=None)
    root.set_metadata("access_policy", "base")
    child = root.add_child("api")
    child.set_metadata("access_policy", "api_auth")
    grandchild = child.add_child("admin")
    grandchild.set_metadata("access_policy", "admin_only")

    result = grandchild.get_effective_access_policy()

    assert isinstance(result, list), f"Expected list, got {type(result)}"
    assert len(result) == 3, f"Expected 3 policies, got {len(result)}"
    assert "base" in result
    assert "api_auth" in result
    assert "admin_only" in result


# ============================================================================
# get_effective_tags tests
# ============================================================================

def test_effective_tags_returns_empty_when_no_tags():
    """
        Returns empty list when no tags are set in the chain.
    """
    root = URLNode(segment="", path="/", parent=None)
    child = root.add_child("api")

    result = child.get_effective_tags()

    assert result == [], f"Expected [], got {result!r}"


def test_effective_tags_returns_own_tags():
    """
        Returns the node's own tags when only it has tags.
    """
    root = URLNode(segment="", path="/", parent=None)
    child = root.add_child("api")
    child.set_metadata("tags", ["internal"])

    result = child.get_effective_tags()

    assert result == ["internal"], f"Expected ['internal'], got {result!r}"


def test_effective_tags_merges_parent_and_child_tags():
    """
        Merges parent and child tags via union.
    """
    root = URLNode(segment="", path="/", parent=None)
    root.set_metadata("tags", ["public"])
    child = root.add_child("api")
    child.set_metadata("tags", ["internal"])

    result = child.get_effective_tags()

    assert "public" in result, "Expected 'public' in merged tags"
    assert "internal" in result, "Expected 'internal' in merged tags"
    assert len(result) == 2, f"Expected 2 tags, got {len(result)}"


def test_effective_tags_deduplicates():
    """
        Duplicate tags across levels are deduplicated.
    """
    root = URLNode(segment="", path="/", parent=None)
    root.set_metadata("tags", ["api", "v1"])
    child = root.add_child("api")
    child.set_metadata("tags", ["api", "internal"])

    result = child.get_effective_tags()

    assert sorted(result) == ["api", "internal", "v1"], f"Expected deduplicated tags, got {result!r}"


def test_effective_tags_replace_tags_true():
    """
        When replace_tags=True, only the node's own tags are returned.
    """
    root = URLNode(segment="", path="/", parent=None)
    root.set_metadata("tags", ["public", "v1"])
    child = root.add_child("api")
    child.set_metadata("tags", ["internal"])
    child.set_metadata("replace_tags", True)

    result = child.get_effective_tags()

    assert result == ["internal"], f"Expected ['internal'], got {result!r}"


def test_effective_tags_replace_tags_false_merges():
    """
        When replace_tags=False (default), tags are merged.
    """
    root = URLNode(segment="", path="/", parent=None)
    root.set_metadata("tags", ["public"])
    child = root.add_child("api")
    child.set_metadata("tags", ["internal"])
    child.set_metadata("replace_tags", False)

    result = child.get_effective_tags()

    assert "public" in result
    assert "internal" in result


def test_effective_tags_three_level_merge():
    """
        Tags merge across three levels.
    """
    root = URLNode(segment="", path="/", parent=None)
    root.set_metadata("tags", ["base"])
    child = root.add_child("api")
    child.set_metadata("tags", ["api"])
    grandchild = child.add_child("users")
    grandchild.set_metadata("tags", ["users"])

    result = grandchild.get_effective_tags()

    assert sorted(result) == ["api", "base", "users"], f"Expected merged tags, got {result!r}"


def test_effective_tags_sorted_output():
    """
        Tags are returned in sorted order for deterministic results.
    """
    root = URLNode(segment="", path="/", parent=None)
    root.set_metadata("tags", ["zebra", "alpha"])
    child = root.add_child("api")
    child.set_metadata("tags", ["middle"])

    result = child.get_effective_tags()

    assert result == sorted(result), f"Expected sorted tags, got {result!r}"


# ============================================================================
# get_effective_rate_limit tests
# ============================================================================

def test_effective_rate_limit_returns_none_when_not_set():
    """
        Returns None when no rate limit is set in the chain.
    """
    root = URLNode(segment="", path="/", parent=None)
    child = root.add_child("api")

    result = child.get_effective_rate_limit()

    assert result is None, f"Expected None, got {result!r}"


def test_effective_rate_limit_returns_own_value():
    """
        Returns the node's own rate limit when only it has one.
    """
    root = URLNode(segment="", path="/", parent=None)
    child = root.add_child("api")
    child.set_metadata("rate_limit", 100)

    result = child.get_effective_rate_limit()

    assert result == 100, f"Expected 100, got {result!r}"


def test_effective_rate_limit_inherits_from_parent():
    """
        Inherits rate limit from parent when not set locally.
    """
    root = URLNode(segment="", path="/", parent=None)
    root.set_metadata("rate_limit", 1000)
    child = root.add_child("api")

    result = child.get_effective_rate_limit()

    assert result == 1000, f"Expected 1000, got {result!r}"


def test_effective_rate_limit_most_restrictive_wins():
    """
        The most restrictive (lowest) rate limit in the chain is returned.
    """
    root = URLNode(segment="", path="/", parent=None)
    root.set_metadata("rate_limit", 1000)
    child = root.add_child("api")
    child.set_metadata("rate_limit", 100)

    result = child.get_effective_rate_limit()

    assert result == 100, f"Expected 100 (most restrictive), got {result!r}"


def test_effective_rate_limit_parent_more_restrictive():
    """
        Parent's more restrictive limit is used even if child has a higher one.
    """
    root = URLNode(segment="", path="/", parent=None)
    root.set_metadata("rate_limit", 50)
    child = root.add_child("api")
    child.set_metadata("rate_limit", 200)

    result = child.get_effective_rate_limit()

    assert result == 50, f"Expected 50 (parent more restrictive), got {result!r}"


def test_effective_rate_limit_explicit_none_opts_out():
    """
        When a child explicitly sets rate_limit=None, it opts out of rate limiting.
    """
    root = URLNode(segment="", path="/", parent=None)
    root.set_metadata("rate_limit", 1000)
    child = root.add_child("api")
    child.set_metadata("rate_limit", None)

    result = child.get_effective_rate_limit()

    assert result is None, f"Expected None (opted out), got {result!r}"


def test_effective_rate_limit_three_level_most_restrictive():
    """
        Most restrictive limit across three levels is returned.
    """
    root = URLNode(segment="", path="/", parent=None)
    root.set_metadata("rate_limit", 1000)
    child = root.add_child("api")
    child.set_metadata("rate_limit", 500)
    grandchild = child.add_child("users")
    grandchild.set_metadata("rate_limit", 100)

    result = grandchild.get_effective_rate_limit()

    assert result == 100, f"Expected 100 (most restrictive), got {result!r}"


def test_effective_rate_limit_middle_most_restrictive():
    """
        Middle node has the most restrictive limit.
    """
    root = URLNode(segment="", path="/", parent=None)
    root.set_metadata("rate_limit", 500)
    child = root.add_child("api")
    child.set_metadata("rate_limit", 10)
    grandchild = child.add_child("users")
    grandchild.set_metadata("rate_limit", 200)

    result = grandchild.get_effective_rate_limit()

    assert result == 10, f"Expected 10 (middle most restrictive), got {result!r}"


# ============================================================================
# Property-Based Tests for Inheritance Resolution
# ============================================================================

import random
import string


def _generate_literal_segment() -> str:
    """
        Generate a valid literal path segment for testing.

        :returns: A valid literal segment string (alphanumeric with underscores/hyphens).
    """
    length = random.randint(1, 12)
    chars = string.ascii_lowercase + string.digits + "_"
    first_char = random.choice(string.ascii_lowercase)
    rest = "".join(random.choice(chars) for _ in range(length - 1))
    return first_char + rest


def _generate_metadata_key() -> str:
    """
        Generate a random metadata key for testing.

        :returns: A valid metadata key string.
    """
    keys = [
        "version", "description", "owner", "priority", "region",
        "tier", "env", "category", "label", "mode",
    ]
    return random.choice(keys)


def _generate_metadata_value() -> str:
    """
        Generate a random non-None metadata value for testing.

        :returns: A non-None string value.
    """
    length = random.randint(1, 8)
    return "".join(random.choice(string.ascii_lowercase) for _ in range(length))


def _build_random_chain(max_depth: int = 5) -> list:
    """
        Build a random linear chain of URLNode instances from root to leaf.

        :param max_depth: Maximum depth of the chain (excluding root).

        :returns: List of URLNode instances from root to leaf.
    """
    depth = random.randint(1, max_depth)
    root = URLNode(segment="", path="/", parent=None)
    chain = [root]

    current = root
    used_segments = set()

    for _ in range(depth):
        segment = _generate_literal_segment()
        while segment in used_segments:
            segment = _generate_literal_segment()
        used_segments.add(segment)

        child = current.add_child(segment)
        chain.append(child)
        current = child

    return chain


def _build_random_tree_with_metadata(max_depth: int = 4, max_children: int = 3) -> tuple:
    """
        Build a random tree and collect all nodes.

        :param max_depth: Maximum depth of the tree.
        :param max_children: Maximum children per node.

        :returns: Tuple of (root, list_of_all_nodes).
    """
    root = URLNode(segment="", path="/", parent=None)
    all_nodes = [root]

    def add_children(node, current_depth):
        if current_depth >= max_depth:
            return

        num_children = random.randint(0, max_children)
        used_segments = set()

        for _ in range(num_children):
            segment = _generate_literal_segment()
            while segment in used_segments or segment in node.children:
                segment = _generate_literal_segment()
            used_segments.add(segment)

            child = node.add_child(segment)
            all_nodes.append(child)
            add_children(child, current_depth + 1)

    add_children(root, 0)
    return root, all_nodes


def _compute_expected_effective_metadata(node, key) -> any:
    """
        Compute the expected effective metadata by walking up the ancestor chain.

        This is the reference implementation used to verify get_effective_metadata.

        :param node: The URLNode to start from.
        :param key: The metadata key to resolve.

        :returns: The expected effective value, or None.
    """
    current = node
    while current is not None:
        value = current.metadata.get(key)
        if value is not None:
            return value
        current = current.parent
    return None


def test_property_inheritance_resolution():
    """
        Property 5: Inheritance Resolution

        *For any* node and metadata key, `get_effective_metadata(key)` SHALL return
        the node's own value if set, otherwise the nearest ancestor's value,
        otherwise None.

        **Validates: Requirements 4.1, 4.2**

        This test generates random tree structures with metadata assigned at
        various levels and verifies that inheritance resolution returns the
        correct value for every node and key combination.
    """
    num_iterations = 100

    for iteration in range(num_iterations):
        random.seed(iteration * 77777)

        # Build a random tree
        root, all_nodes = _build_random_tree_with_metadata(
            max_depth=4, max_children=3
        )

        # Assign metadata to random nodes at various levels
        key = _generate_metadata_key()
        nodes_with_metadata = random.sample(
            all_nodes,
            k=random.randint(0, len(all_nodes))
        )

        for node in nodes_with_metadata:
            value = _generate_metadata_value()
            node.set_metadata(key, value)

        # Verify inheritance resolution for every node in the tree
        for node in all_nodes:
            actual = node.get_effective_metadata(key)
            expected = _compute_expected_effective_metadata(node, key)

            if actual != expected:
                errmsg = (
                    f"Iteration {iteration}: Inheritance resolution mismatch "
                    f"for key '{key}' at path '{node.path}'. "
                    f"Expected {expected!r}, got {actual!r}"
                )
                raise AssertionError(errmsg)

    return


def test_property_inheritance_own_value_takes_precedence():
    """
        Property 5: Inheritance Resolution - Own Value Precedence

        *For any* node that has its own metadata value set for a key,
        `get_effective_metadata(key)` SHALL return that node's own value
        regardless of what ancestors have set.

        **Validates: Requirements 4.1, 4.2**
    """
    num_iterations = 100

    for iteration in range(num_iterations):
        random.seed(iteration * 88888)

        # Build a random chain
        chain = _build_random_chain(max_depth=6)

        key = _generate_metadata_key()

        # Set metadata on random ancestors
        for node in chain[:-1]:
            if random.random() < 0.5:
                node.set_metadata(key, _generate_metadata_value())

        # Set a specific value on the leaf node
        leaf = chain[-1]
        leaf_value = "leaf_own_value_" + str(iteration)
        leaf.set_metadata(key, leaf_value)

        # The leaf's own value must take precedence
        actual = leaf.get_effective_metadata(key)

        if actual != leaf_value:
            errmsg = (
                f"Iteration {iteration}: Leaf node's own value should take "
                f"precedence. Expected {leaf_value!r}, got {actual!r}. "
                f"Path: {leaf.path}"
            )
            raise AssertionError(errmsg)

    return


def test_property_inheritance_nearest_ancestor_wins():
    """
        Property 5: Inheritance Resolution - Nearest Ancestor

        *For any* node without its own metadata value, `get_effective_metadata(key)`
        SHALL return the nearest ancestor's value (not a more distant ancestor).

        **Validates: Requirements 4.1, 4.2**
    """
    num_iterations = 100

    for iteration in range(num_iterations):
        random.seed(iteration * 99999)

        # Build a chain of at least 3 nodes
        chain = _build_random_chain(max_depth=6)
        if len(chain) < 3:
            continue

        key = _generate_metadata_key()

        # Pick a random node in the chain (not root, not the one right after root)
        target_idx = random.randint(2, len(chain) - 1)
        target_node = chain[target_idx]

        # Set metadata on a distant ancestor
        distant_idx = random.randint(0, target_idx - 2) if target_idx >= 2 else 0
        distant_value = "distant_" + str(iteration)
        chain[distant_idx].set_metadata(key, distant_value)

        # Set metadata on the nearest ancestor (one level up from target)
        nearest_value = "nearest_" + str(iteration)
        chain[target_idx - 1].set_metadata(key, nearest_value)

        # Do NOT set metadata on the target node itself

        actual = target_node.get_effective_metadata(key)

        if actual != nearest_value:
            errmsg = (
                f"Iteration {iteration}: Expected nearest ancestor value "
                f"{nearest_value!r}, got {actual!r}. "
                f"Target path: {target_node.path}, "
                f"Nearest ancestor path: {chain[target_idx - 1].path}"
            )
            raise AssertionError(errmsg)

    return


def test_property_inheritance_returns_none_when_unset():
    """
        Property 5: Inheritance Resolution - None When Unset

        *For any* node and metadata key where no node in the ancestor chain
        defines the key, `get_effective_metadata(key)` SHALL return None.

        **Validates: Requirements 4.1, 4.2**
    """
    num_iterations = 100

    for iteration in range(num_iterations):
        random.seed(iteration * 11111)

        # Build a random tree
        root, all_nodes = _build_random_tree_with_metadata(
            max_depth=4, max_children=3
        )

        # Use a key that is never set on any node
        unset_key = "completely_unset_key_" + str(iteration)

        # Verify every node returns None for the unset key
        for node in all_nodes:
            actual = node.get_effective_metadata(unset_key)

            if actual is not None:
                errmsg = (
                    f"Iteration {iteration}: Expected None for unset key "
                    f"'{unset_key}' at path '{node.path}', got {actual!r}"
                )
                raise AssertionError(errmsg)

    return


# ============================================================================
# Property-Based Tests for Tag Merge Semantics
# ============================================================================


def _generate_tag() -> str:
    """
        Generate a random tag string for testing.

        :returns: A short lowercase alphabetic tag.
    """
    length = random.randint(2, 8)
    return "".join(random.choice(string.ascii_lowercase) for _ in range(length))


def _generate_tag_set(max_size: int = 5) -> list:
    """
        Generate a list of unique random tags.

        :param max_size: Maximum number of tags to generate.

        :returns: A list of unique tag strings.
    """
    count = random.randint(0, max_size)
    tags = set()
    while len(tags) < count:
        tags.add(_generate_tag())
    return list(tags)


def _compute_expected_effective_tags(node) -> list:
    """
        Compute the expected effective tags by walking up the ancestor chain.

        This is the reference implementation used to verify get_effective_tags.
        If the node has replace_tags=True, only its own tags are returned.
        Otherwise, collects the union of all ancestor tags plus the node's own.

        :param node: The URLNode to compute effective tags for.

        :returns: A sorted list of unique tags.
    """
    if node.metadata.get("replace_tags", False):
        own_tags = node.metadata.get("tags", [])
        return sorted(set(own_tags))

    all_tags = set()
    current = node
    while current is not None:
        node_tags = current.metadata.get("tags", [])
        all_tags.update(node_tags)
        current = current.parent

    return sorted(all_tags)


def test_property_tag_merge_union():
    """
        Property 6: Tag Merge Semantics - Union Merge

        *For any* node with replace_tags=False (or unset), get_effective_tags()
        SHALL return the union of all ancestor tags plus the node's own tags.

        **Validates: Requirements 4.4, 4.5**

        This test generates random chains with tags assigned at various levels
        and verifies that the effective tags are the union of all tags in the
        ancestor chain.
    """
    num_iterations = 100

    for iteration in range(num_iterations):
        random.seed(iteration * 12321)

        chain = _build_random_chain(max_depth=6)

        # Assign random tags to random nodes in the chain
        for node in chain:
            if random.random() < 0.6:
                tags = _generate_tag_set(max_size=4)
                node.set_metadata("tags", tags)

        # Verify effective tags for every node in the chain
        for node in chain:
            actual = node.get_effective_tags()
            expected = _compute_expected_effective_tags(node)

            if actual != expected:
                errmsg = (
                    f"Iteration {iteration}: Tag merge mismatch at path "
                    f"'{node.path}'. Expected {expected!r}, got {actual!r}"
                )
                raise AssertionError(errmsg)

    return


def test_property_tag_merge_replace_tags_true():
    """
        Property 6: Tag Merge Semantics - Replace Tags

        *For any* node with replace_tags=True, get_effective_tags() SHALL return
        only the node's own tags, ignoring all ancestor tags.

        **Validates: Requirements 4.4, 4.5**

        This test generates random chains where the leaf node has replace_tags=True
        and verifies that ancestor tags are excluded from the result.
    """
    num_iterations = 100

    for iteration in range(num_iterations):
        random.seed(iteration * 23432)

        chain = _build_random_chain(max_depth=6)

        # Assign tags to all ancestor nodes
        for node in chain[:-1]:
            tags = _generate_tag_set(max_size=4)
            if tags:
                node.set_metadata("tags", tags)

        # Set replace_tags=True on the leaf node with its own tags
        leaf = chain[-1]
        leaf_tags = _generate_tag_set(max_size=4)
        leaf.set_metadata("tags", leaf_tags)
        leaf.set_metadata("replace_tags", True)

        actual = leaf.get_effective_tags()
        expected = sorted(set(leaf_tags))

        if actual != expected:
            errmsg = (
                f"Iteration {iteration}: With replace_tags=True, expected "
                f"only leaf tags {expected!r}, got {actual!r}. "
                f"Path: {leaf.path}"
            )
            raise AssertionError(errmsg)

    return


def test_property_tag_merge_tree_wide():
    """
        Property 6: Tag Merge Semantics - Tree-Wide Verification

        *For any* tree with tags assigned at various levels and mixed
        replace_tags settings, get_effective_tags() SHALL return the correct
        result for every node.

        **Validates: Requirements 4.4, 4.5**
    """
    num_iterations = 100

    for iteration in range(num_iterations):
        random.seed(iteration * 34543)

        root, all_nodes = _build_random_tree_with_metadata(
            max_depth=4, max_children=3
        )

        # Assign tags and replace_tags to random nodes
        for node in all_nodes:
            if random.random() < 0.5:
                tags = _generate_tag_set(max_size=3)
                node.set_metadata("tags", tags)
            if random.random() < 0.2:
                node.set_metadata("replace_tags", True)

        # Verify effective tags for every node
        for node in all_nodes:
            actual = node.get_effective_tags()
            expected = _compute_expected_effective_tags(node)

            if actual != expected:
                errmsg = (
                    f"Iteration {iteration}: Tag merge mismatch at path "
                    f"'{node.path}'. replace_tags="
                    f"{node.metadata.get('replace_tags', False)}. "
                    f"Expected {expected!r}, got {actual!r}"
                )
                raise AssertionError(errmsg)

    return


# ============================================================================
# Property-Based Tests for Rate Limit Restriction
# ============================================================================


def _generate_rate_limit() -> int:
    """
        Generate a random positive rate limit value.

        :returns: A positive integer rate limit.
    """
    return random.randint(1, 10000)


def _compute_expected_effective_rate_limit(node) -> any:
    """
        Compute the expected effective rate limit by walking up the ancestor chain.

        This is the reference implementation used to verify get_effective_rate_limit.
        If the node explicitly sets rate_limit=None (key present, value None), it
        opts out and None is returned. Otherwise, the most restrictive (lowest)
        rate limit in the chain is returned.

        :param node: The URLNode to compute effective rate limit for.

        :returns: The expected effective rate limit, or None.
    """
    # If this node explicitly sets rate_limit to None, it opts out
    node_meta = node.metadata
    if "rate_limit" in node_meta and node_meta["rate_limit"] is None:
        return None

    most_restrictive = None
    current = node
    while current is not None:
        current_meta = current.metadata
        if "rate_limit" in current_meta:
            limit = current_meta["rate_limit"]
            if limit is not None:
                if most_restrictive is None or limit < most_restrictive:
                    most_restrictive = limit
        current = current.parent

    return most_restrictive


def test_property_rate_limit_most_restrictive():
    """
        Property 7: Rate Limit Restriction - Most Restrictive Wins

        *For any* inheritance chain with rate limits, the effective rate limit
        SHALL be the most restrictive (lowest) value.

        **Validates: Requirements 4.7**

        This test generates random chains with rate limits assigned at various
        levels and verifies that the most restrictive limit is returned.
    """
    num_iterations = 100

    for iteration in range(num_iterations):
        random.seed(iteration * 45654)

        chain = _build_random_chain(max_depth=6)

        # Assign rate limits to random nodes
        for node in chain:
            if random.random() < 0.6:
                node.set_metadata("rate_limit", _generate_rate_limit())

        # Verify effective rate limit for every node in the chain
        for node in chain:
            actual = node.get_effective_rate_limit()
            expected = _compute_expected_effective_rate_limit(node)

            if actual != expected:
                errmsg = (
                    f"Iteration {iteration}: Rate limit mismatch at path "
                    f"'{node.path}'. Expected {expected!r}, got {actual!r}"
                )
                raise AssertionError(errmsg)

    return


def test_property_rate_limit_explicit_none_opts_out():
    """
        Property 7: Rate Limit Restriction - Explicit None Opts Out

        *For any* node that explicitly sets rate_limit=None, the effective
        rate limit SHALL be None regardless of ancestor rate limits.

        **Validates: Requirements 4.7**

        This test generates random chains where the leaf node explicitly sets
        rate_limit=None and verifies that None is returned.
    """
    num_iterations = 100

    for iteration in range(num_iterations):
        random.seed(iteration * 56765)

        chain = _build_random_chain(max_depth=6)

        # Assign rate limits to all ancestor nodes
        for node in chain[:-1]:
            node.set_metadata("rate_limit", _generate_rate_limit())

        # Explicitly set rate_limit=None on the leaf
        leaf = chain[-1]
        leaf.set_metadata("rate_limit", None)

        actual = leaf.get_effective_rate_limit()

        if actual is not None:
            errmsg = (
                f"Iteration {iteration}: With explicit rate_limit=None, "
                f"expected None, got {actual!r}. Path: {leaf.path}"
            )
            raise AssertionError(errmsg)

    return


def test_property_rate_limit_tree_wide():
    """
        Property 7: Rate Limit Restriction - Tree-Wide Verification

        *For any* tree with rate limits assigned at various levels (including
        explicit None opt-outs), get_effective_rate_limit() SHALL return the
        correct result for every node.

        **Validates: Requirements 4.7**
    """
    num_iterations = 100

    for iteration in range(num_iterations):
        random.seed(iteration * 67876)

        root, all_nodes = _build_random_tree_with_metadata(
            max_depth=4, max_children=3
        )

        # Assign rate limits to random nodes, including some explicit None
        for node in all_nodes:
            roll = random.random()
            if roll < 0.4:
                node.set_metadata("rate_limit", _generate_rate_limit())
            elif roll < 0.5:
                node.set_metadata("rate_limit", None)

        # Verify effective rate limit for every node
        for node in all_nodes:
            actual = node.get_effective_rate_limit()
            expected = _compute_expected_effective_rate_limit(node)

            if actual != expected:
                errmsg = (
                    f"Iteration {iteration}: Rate limit mismatch at path "
                    f"'{node.path}'. Expected {expected!r}, got {actual!r}"
                )
                raise AssertionError(errmsg)

    return
