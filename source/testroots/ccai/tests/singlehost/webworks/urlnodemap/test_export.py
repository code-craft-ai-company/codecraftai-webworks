"""
    Tests for the URLNodeMap export methods.

    This module contains unit tests for export_tree(), export_routes(),
    and export_security_map() methods on the URLNodeMap class.
"""

from ccai.webworks.urlnodemap.urlnodemap import URLNodeMap


# =============================================================================
# Helper Handlers
# =============================================================================

def _get_handler():
    """Dummy GET handler for testing."""
    return


def _post_handler():
    """Dummy POST handler for testing."""
    return


def _put_handler():
    """Dummy PUT handler for testing."""
    return


def _delete_handler():
    """Dummy DELETE handler for testing."""
    return


# =============================================================================
# Unit Tests for export_tree()
# =============================================================================

def test_export_tree_empty_map():
    """
        Test that export_tree on an empty map returns root node dict.

        Validates: Requirements 6.1
    """
    node_map = URLNodeMap()

    result = node_map.export_tree()

    if result["segment"] != "":
        errmsg = f"Expected root segment '', got '{result['segment']}'"
        raise AssertionError(errmsg)

    if result["path"] != "/":
        errmsg = f"Expected root path '/', got '{result['path']}'"
        raise AssertionError(errmsg)

    if len(result["children"]) != 0:
        errmsg = f"Expected 0 children, got {len(result['children'])}"
        raise AssertionError(errmsg)

    return


def test_export_tree_single_child():
    """
        Test that export_tree includes a single child node.

        Validates: Requirements 6.1
    """
    node_map = URLNodeMap()
    node_map.get_or_create_node("/api")

    result = node_map.export_tree()

    if "api" not in result["children"]:
        errmsg = "Expected 'api' in root children"
        raise AssertionError(errmsg)

    api_node = result["children"]["api"]

    if api_node["segment"] != "api":
        errmsg = f"Expected segment 'api', got '{api_node['segment']}'"
        raise AssertionError(errmsg)

    if api_node["path"] != "/api":
        errmsg = f"Expected path '/api', got '{api_node['path']}'"
        raise AssertionError(errmsg)

    return


def test_export_tree_nested_structure():
    """
        Test that export_tree correctly serializes a nested tree.

        Validates: Requirements 6.1
    """
    node_map = URLNodeMap()
    node_map.get_or_create_node("/api/v1/users")

    result = node_map.export_tree()

    api_node = result["children"]["api"]
    v1_node = api_node["children"]["v1"]
    users_node = v1_node["children"]["users"]

    if users_node["path"] != "/api/v1/users":
        errmsg = f"Expected path '/api/v1/users', got '{users_node['path']}'"
        raise AssertionError(errmsg)

    return


def test_export_tree_includes_metadata():
    """
        Test that export_tree includes node metadata.

        Validates: Requirements 6.1
    """
    node_map = URLNodeMap()
    node = node_map.get_or_create_node("/api")
    node.set_metadata("version", "v1")

    result = node_map.export_tree()
    api_node = result["children"]["api"]

    if api_node["metadata"].get("version") != "v1":
        errmsg = f"Expected metadata version 'v1', got '{api_node['metadata'].get('version')}'"
        raise AssertionError(errmsg)

    return


def test_export_tree_includes_handlers():
    """
        Test that export_tree includes handler method names.

        Validates: Requirements 6.1
    """
    node_map = URLNodeMap()
    node = node_map.get_or_create_node("/api/users")
    node.attach_handler("GET", _get_handler)
    node.attach_handler("POST", _post_handler)

    result = node_map.export_tree()
    users_node = result["children"]["api"]["children"]["users"]

    if "GET" not in users_node["handlers"]:
        errmsg = "Expected 'GET' in handlers"
        raise AssertionError(errmsg)

    if "POST" not in users_node["handlers"]:
        errmsg = "Expected 'POST' in handlers"
        raise AssertionError(errmsg)

    return


def test_export_tree_parameter_segment():
    """
        Test that export_tree marks parameter segments.

        Validates: Requirements 6.1
    """
    node_map = URLNodeMap()
    node_map.get_or_create_node("/api/users/{user_id}")

    result = node_map.export_tree()
    user_id_node = result["children"]["api"]["children"]["users"]["children"]["{user_id}"]

    if user_id_node["is_parameter"] is not True:
        errmsg = "Expected is_parameter to be True for {user_id}"
        raise AssertionError(errmsg)

    return


# =============================================================================
# Unit Tests for export_routes()
# =============================================================================

def test_export_routes_empty_map():
    """
        Test that export_routes returns empty list for map with no handlers.

        Validates: Requirements 6.2
    """
    node_map = URLNodeMap()
    node_map.get_or_create_node("/api/v1")

    routes = node_map.export_routes()

    if len(routes) != 0:
        errmsg = f"Expected 0 routes, got {len(routes)}"
        raise AssertionError(errmsg)

    return


def test_export_routes_single_route():
    """
        Test that export_routes returns one entry for a single leaf.

        Validates: Requirements 6.2, 6.3
    """
    node_map = URLNodeMap()
    node = node_map.get_or_create_node("/api/users")
    node.attach_handler("GET", _get_handler)

    routes = node_map.export_routes()

    if len(routes) != 1:
        errmsg = f"Expected 1 route, got {len(routes)}"
        raise AssertionError(errmsg)

    route = routes[0]

    if route["path"] != "/api/users":
        errmsg = f"Expected path '/api/users', got '{route['path']}'"
        raise AssertionError(errmsg)

    if route["methods"] != ["GET"]:
        errmsg = f"Expected methods ['GET'], got {route['methods']}"
        raise AssertionError(errmsg)

    if route["handler"] != "_get_handler":
        errmsg = f"Expected handler '_get_handler', got '{route['handler']}'"
        raise AssertionError(errmsg)

    return


def test_export_routes_multiple_methods():
    """
        Test that export_routes includes all methods for a node.

        Validates: Requirements 6.2, 6.3
    """
    node_map = URLNodeMap()
    node = node_map.get_or_create_node("/api/users")
    node.attach_handler("GET", _get_handler)
    node.attach_handler("POST", _post_handler)

    routes = node_map.export_routes()

    if len(routes) != 1:
        errmsg = f"Expected 1 route, got {len(routes)}"
        raise AssertionError(errmsg)

    route = routes[0]

    if route["methods"] != ["GET", "POST"]:
        errmsg = f"Expected methods ['GET', 'POST'], got {route['methods']}"
        raise AssertionError(errmsg)

    return


def test_export_routes_multiple_leaves():
    """
        Test that export_routes returns one entry per leaf.

        Validates: Requirements 6.2
    """
    node_map = URLNodeMap()

    users_node = node_map.get_or_create_node("/api/users")
    users_node.attach_handler("GET", _get_handler)

    items_node = node_map.get_or_create_node("/api/items")
    items_node.attach_handler("GET", _get_handler)

    routes = node_map.export_routes()

    if len(routes) != 2:
        errmsg = f"Expected 2 routes, got {len(routes)}"
        raise AssertionError(errmsg)

    paths = [r["path"] for r in routes]

    if "/api/users" not in paths:
        errmsg = "Expected '/api/users' in exported routes"
        raise AssertionError(errmsg)

    if "/api/items" not in paths:
        errmsg = "Expected '/api/items' in exported routes"
        raise AssertionError(errmsg)

    return


def test_export_routes_resolves_inherited_tags():
    """
        Test that export_routes resolves inherited tags.

        Validates: Requirements 6.3, 6.8
    """
    node_map = URLNodeMap()

    api_node = node_map.get_or_create_node("/api")
    api_node.set_metadata("tags", ["api"])

    users_node = node_map.get_or_create_node("/api/users")
    users_node.set_metadata("tags", ["users"])
    users_node.attach_handler("GET", _get_handler)

    routes = node_map.export_routes()
    route = routes[0]

    if "api" not in route["tags"]:
        errmsg = f"Expected 'api' in tags, got {route['tags']}"
        raise AssertionError(errmsg)

    if "users" not in route["tags"]:
        errmsg = f"Expected 'users' in tags, got {route['tags']}"
        raise AssertionError(errmsg)

    return


def test_export_routes_resolves_inherited_access_policy():
    """
        Test that export_routes resolves inherited access policy.

        Validates: Requirements 6.3, 6.8
    """
    node_map = URLNodeMap()

    api_node = node_map.get_or_create_node("/api")
    api_node.set_metadata("access_policy", "authenticated")

    users_node = node_map.get_or_create_node("/api/users")
    users_node.attach_handler("GET", _get_handler)

    routes = node_map.export_routes()
    route = routes[0]

    if route["access_policy"] != "authenticated":
        errmsg = f"Expected access_policy 'authenticated', got '{route['access_policy']}'"
        raise AssertionError(errmsg)

    return


def test_export_routes_resolves_inherited_rate_limit():
    """
        Test that export_routes resolves inherited rate limit.

        Validates: Requirements 6.3, 6.8
    """
    node_map = URLNodeMap()

    api_node = node_map.get_or_create_node("/api")
    api_node.set_metadata("rate_limit", 100)

    users_node = node_map.get_or_create_node("/api/users")
    users_node.set_metadata("rate_limit", 50)
    users_node.attach_handler("GET", _get_handler)

    routes = node_map.export_routes()
    route = routes[0]

    if route["rate_limit"] != "50":
        errmsg = f"Expected rate_limit '50', got '{route['rate_limit']}'"
        raise AssertionError(errmsg)

    return


def test_export_routes_includes_version():
    """
        Test that export_routes includes version metadata.

        Validates: Requirements 6.3
    """
    node_map = URLNodeMap()

    api_node = node_map.get_or_create_node("/api")
    api_node.set_metadata("version", "v2")

    users_node = node_map.get_or_create_node("/api/users")
    users_node.attach_handler("GET", _get_handler)

    routes = node_map.export_routes()
    route = routes[0]

    if route["version"] != "v2":
        errmsg = f"Expected version 'v2', got '{route['version']}'"
        raise AssertionError(errmsg)

    return


def test_export_routes_includes_scopes():
    """
        Test that export_routes includes scopes metadata.

        Validates: Requirements 6.3
    """
    node_map = URLNodeMap()

    users_node = node_map.get_or_create_node("/api/users")
    users_node.set_metadata("scopes", ["read:users", "write:users"])
    users_node.attach_handler("GET", _get_handler)

    routes = node_map.export_routes()
    route = routes[0]

    if route["scopes"] != ["read:users", "write:users"]:
        errmsg = f"Expected scopes ['read:users', 'write:users'], got {route['scopes']}"
        raise AssertionError(errmsg)

    return


def test_export_routes_includes_extras():
    """
        Test that export_routes includes extras metadata.

        Validates: Requirements 6.3
    """
    node_map = URLNodeMap()

    users_node = node_map.get_or_create_node("/api/users")
    users_node.set_metadata("extras", {"deprecated": True})
    users_node.attach_handler("GET", _get_handler)

    routes = node_map.export_routes()
    route = routes[0]

    if route["extras"] != {"deprecated": True}:
        errmsg = f"Expected extras {{'deprecated': True}}, got {route['extras']}"
        raise AssertionError(errmsg)

    return


# =============================================================================
# Unit Tests for export_security_map()
# =============================================================================

def test_export_security_map_empty_map():
    """
        Test that export_security_map returns empty list for map with no handlers.

        Validates: Requirements 6.4
    """
    node_map = URLNodeMap()
    node_map.get_or_create_node("/api")

    entries = node_map.export_security_map()

    if len(entries) != 0:
        errmsg = f"Expected 0 entries, got {len(entries)}"
        raise AssertionError(errmsg)

    return


def test_export_security_map_single_route():
    """
        Test that export_security_map returns entry for a single leaf.

        Validates: Requirements 6.4, 6.5
    """
    node_map = URLNodeMap()
    node = node_map.get_or_create_node("/api/users")
    node.attach_handler("GET", _get_handler)
    node.set_metadata("access_policy", "public")
    node.set_metadata("scopes", ["read:users"])

    entries = node_map.export_security_map()

    if len(entries) != 1:
        errmsg = f"Expected 1 entry, got {len(entries)}"
        raise AssertionError(errmsg)

    entry = entries[0]

    if entry["path"] != "/api/users":
        errmsg = f"Expected path '/api/users', got '{entry['path']}'"
        raise AssertionError(errmsg)

    if entry["methods"] != ["GET"]:
        errmsg = f"Expected methods ['GET'], got {entry['methods']}"
        raise AssertionError(errmsg)

    if entry["handler"] != "_get_handler":
        errmsg = f"Expected handler '_get_handler', got '{entry['handler']}'"
        raise AssertionError(errmsg)

    if entry["access_policy"] != "public":
        errmsg = f"Expected access_policy 'public', got '{entry['access_policy']}'"
        raise AssertionError(errmsg)

    if entry["scopes"] != ["read:users"]:
        errmsg = f"Expected scopes ['read:users'], got {entry['scopes']}"
        raise AssertionError(errmsg)

    return


def test_export_security_map_filter_by_tag():
    """
        Test that export_security_map filters by tag when provided.

        Validates: Requirements 6.6
    """
    node_map = URLNodeMap()

    users_node = node_map.get_or_create_node("/api/users")
    users_node.set_metadata("tags", ["public"])
    users_node.attach_handler("GET", _get_handler)

    admin_node = node_map.get_or_create_node("/api/admin")
    admin_node.set_metadata("tags", ["internal"])
    admin_node.attach_handler("GET", _get_handler)

    entries = node_map.export_security_map(filter_tag="public")

    if len(entries) != 1:
        errmsg = f"Expected 1 entry with tag 'public', got {len(entries)}"
        raise AssertionError(errmsg)

    if entries[0]["path"] != "/api/users":
        errmsg = f"Expected path '/api/users', got '{entries[0]['path']}'"
        raise AssertionError(errmsg)

    return


def test_export_security_map_filter_no_match():
    """
        Test that export_security_map returns empty when no routes match tag.

        Validates: Requirements 6.6
    """
    node_map = URLNodeMap()

    users_node = node_map.get_or_create_node("/api/users")
    users_node.set_metadata("tags", ["public"])
    users_node.attach_handler("GET", _get_handler)

    entries = node_map.export_security_map(filter_tag="internal")

    if len(entries) != 0:
        errmsg = f"Expected 0 entries, got {len(entries)}"
        raise AssertionError(errmsg)

    return


def test_export_security_map_no_filter_returns_all():
    """
        Test that export_security_map without filter returns all routes.

        Validates: Requirements 6.4
    """
    node_map = URLNodeMap()

    users_node = node_map.get_or_create_node("/api/users")
    users_node.set_metadata("tags", ["public"])
    users_node.attach_handler("GET", _get_handler)

    admin_node = node_map.get_or_create_node("/api/admin")
    admin_node.set_metadata("tags", ["internal"])
    admin_node.attach_handler("GET", _get_handler)

    entries = node_map.export_security_map()

    if len(entries) != 2:
        errmsg = f"Expected 2 entries, got {len(entries)}"
        raise AssertionError(errmsg)

    return


def test_export_security_map_includes_summary():
    """
        Test that export_security_map includes a summary field.

        Validates: Requirements 6.5
    """
    node_map = URLNodeMap()

    node = node_map.get_or_create_node("/api/users")
    node.attach_handler("GET", _get_handler)
    node.set_metadata("access_policy", "authenticated")

    entries = node_map.export_security_map()
    entry = entries[0]

    if "summary" not in entry:
        errmsg = "Expected 'summary' key in security map entry"
        raise AssertionError(errmsg)

    if "GET" not in entry["summary"]:
        errmsg = f"Expected 'GET' in summary, got '{entry['summary']}'"
        raise AssertionError(errmsg)

    if "/api/users" not in entry["summary"]:
        errmsg = f"Expected '/api/users' in summary, got '{entry['summary']}'"
        raise AssertionError(errmsg)

    return


def test_export_security_map_inherited_access_policy():
    """
        Test that export_security_map resolves inherited access policy.

        Validates: Requirements 6.5, 6.8
    """
    node_map = URLNodeMap()

    api_node = node_map.get_or_create_node("/api")
    api_node.set_metadata("access_policy", "authenticated")

    users_node = node_map.get_or_create_node("/api/users")
    users_node.attach_handler("GET", _get_handler)

    entries = node_map.export_security_map()
    entry = entries[0]

    if entry["access_policy"] != "authenticated":
        errmsg = f"Expected access_policy 'authenticated', got '{entry['access_policy']}'"
        raise AssertionError(errmsg)

    return


def test_export_security_map_inherited_tags_for_filter():
    """
        Test that export_security_map uses inherited tags for filtering.

        Validates: Requirements 6.6, 6.8
    """
    node_map = URLNodeMap()

    api_node = node_map.get_or_create_node("/api")
    api_node.set_metadata("tags", ["public"])

    users_node = node_map.get_or_create_node("/api/users")
    users_node.attach_handler("GET", _get_handler)

    entries = node_map.export_security_map(filter_tag="public")

    if len(entries) != 1:
        errmsg = f"Expected 1 entry (inherited tag 'public'), got {len(entries)}"
        raise AssertionError(errmsg)

    return


def test_export_security_map_rate_limit():
    """
        Test that export_security_map includes rate limit info.

        Validates: Requirements 6.5
    """
    node_map = URLNodeMap()

    node = node_map.get_or_create_node("/api/users")
    node.set_metadata("rate_limit", 100)
    node.attach_handler("GET", _get_handler)

    entries = node_map.export_security_map()
    entry = entries[0]

    if entry["rate_limit"] != "100":
        errmsg = f"Expected rate_limit '100', got '{entry['rate_limit']}'"
        raise AssertionError(errmsg)

    return


# =============================================================================
# Random Data Generators for Property Tests
# =============================================================================

import random
import string


def _generate_random_segment(min_length=1, max_length=10):
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


def _generate_random_path(min_segments=1, max_segments=4):
    """
        Generate a random valid normalized path string.

        :returns: A normalized path string (e.g., "/api/v1/users").
    """
    num_segments = random.randint(min_segments, max_segments)
    segments = [_generate_random_segment() for _ in range(num_segments)]
    return "/" + "/".join(segments)


def _generate_distinct_paths(count, min_segments=1, max_segments=4):
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


def _generate_random_tags():
    """
        Generate a random list of tag strings.

        :returns: A list of 0-3 random tag strings.
    """
    tag_pool = ["api", "public", "internal", "admin", "v1", "v2", "beta",
                "deprecated", "stable", "auth", "readonly", "write"]
    count = random.randint(0, 3)
    return random.sample(tag_pool, min(count, len(tag_pool)))


def _generate_random_access_policy():
    """
        Generate a random access policy string or None.

        :returns: A string access policy or None.
    """
    policies = [None, "public", "authenticated", "admin", "internal"]
    return random.choice(policies)


def _generate_random_rate_limit():
    """
        Generate a random rate limit integer or None.

        :returns: An integer rate limit or None.
    """
    if random.random() < 0.4:
        return None
    return random.randint(1, 1000)


def _generate_random_metadata():
    """
        Generate a random metadata dictionary with tags, access_policy,
        rate_limit, version, scopes, and extras.

        :returns: A dictionary of metadata key-value pairs.
    """
    metadata = {}

    if random.random() < 0.5:
        metadata["tags"] = _generate_random_tags()

    if random.random() < 0.4:
        metadata["access_policy"] = _generate_random_access_policy()

    if random.random() < 0.4:
        metadata["rate_limit"] = _generate_random_rate_limit()

    if random.random() < 0.3:
        versions = ["v1", "v2", "v3", None]
        metadata["version"] = random.choice(versions)

    if random.random() < 0.3:
        scope_pool = ["read:users", "write:users", "admin:all", "read:items"]
        count = random.randint(0, 2)
        metadata["scopes"] = random.sample(scope_pool, count)

    if random.random() < 0.2:
        metadata["extras"] = {"custom_key": _generate_random_segment(3, 8)}

    return metadata


def _dummy_handler():
    """Dummy handler for property test leaf nodes."""
    return


# =============================================================================
# Property-Based Tests
# =============================================================================

# Feature: url-node-map, Property 9: Export Consistency
# *For any* URL Node Map, `export_routes()` SHALL return one entry for each
# leaf node, and each entry's metadata SHALL match `get_effective_metadata()`
# for that node.
# **Validates: Requirements 6.2, 6.3, 6.8**


def test_property_9_export_consistency_route_count_matches_leaves():
    """
        Property 9: Export Consistency - Route count matches leaf count

        For any URL Node Map populated with random paths, handlers, and
        metadata, export_routes() SHALL return exactly one entry for each
        leaf node. The number of exported routes must equal the number of
        leaf nodes in the tree.

        **Validates: Requirements 6.2, 6.3**
    """
    for iteration in range(100):
        random.seed(iteration * 99991)

        node_map = URLNodeMap()

        # Generate random tree structure
        num_paths = random.randint(1, 12)
        paths = _generate_distinct_paths(num_paths, min_segments=1, max_segments=4)

        for path in paths:
            node = node_map.get_or_create_node(path)
            # Apply random metadata to some nodes
            metadata = _generate_random_metadata()
            for key, value in metadata.items():
                node.set_metadata(key, value)

        # Attach handlers to a random subset to create leaves
        all_nodes = list(node_map.iterate_nodes())
        non_leaf_nodes = [n for n in all_nodes if not n.is_leaf]
        if len(non_leaf_nodes) > 0:
            num_handlers = random.randint(1, max(1, len(non_leaf_nodes)))
            handler_nodes = random.sample(non_leaf_nodes, num_handlers)
            for node in handler_nodes:
                node.attach_handler("GET", _dummy_handler)

        # Count actual leaves
        leaf_nodes = [n for n in node_map.iterate_nodes() if n.is_leaf]
        leaf_count = len(leaf_nodes)

        # Export routes
        routes = node_map.export_routes()

        if len(routes) != leaf_count:
            errmsg = (
                f"Iteration {iteration}: export_routes() returned {len(routes)} "
                f"routes but tree has {leaf_count} leaf nodes.\n"
                f"  Inserted paths: {paths}\n"
                f"  Leaf paths: {[n.path for n in leaf_nodes]}\n"
                f"  Exported paths: {[r['path'] for r in routes]}"
            )
            raise AssertionError(errmsg)

    return


def test_property_9_export_consistency_leaf_paths_in_export():
    """
        Property 9: Export Consistency - Each leaf path appears in export

        For any URL Node Map, every leaf node's path SHALL appear in the
        export_routes() output. No leaf path shall be missing from the
        exported routes.

        **Validates: Requirements 6.2, 6.3**
    """
    for iteration in range(100):
        random.seed(iteration * 88883)

        node_map = URLNodeMap()

        # Generate random tree
        num_paths = random.randint(1, 10)
        paths = _generate_distinct_paths(num_paths, min_segments=1, max_segments=4)

        for path in paths:
            node = node_map.get_or_create_node(path)
            metadata = _generate_random_metadata()
            for key, value in metadata.items():
                node.set_metadata(key, value)

        # Attach handlers to create leaves
        all_nodes = list(node_map.iterate_nodes())
        non_leaf_nodes = [n for n in all_nodes if not n.is_leaf]
        if len(non_leaf_nodes) > 0:
            num_handlers = random.randint(1, max(1, len(non_leaf_nodes)))
            handler_nodes = random.sample(non_leaf_nodes, num_handlers)
            for node in handler_nodes:
                node.attach_handler("GET", _dummy_handler)

        # Collect leaf paths
        leaf_paths = {n.path for n in node_map.iterate_nodes() if n.is_leaf}

        # Export routes
        routes = node_map.export_routes()
        exported_paths = {r["path"] for r in routes}

        if leaf_paths != exported_paths:
            missing = leaf_paths - exported_paths
            extra = exported_paths - leaf_paths
            errmsg = (
                f"Iteration {iteration}: export path set mismatch.\n"
                f"  Missing leaf paths: {missing}\n"
                f"  Extra exported paths: {extra}\n"
                f"  Inserted paths: {paths}"
            )
            raise AssertionError(errmsg)

    return


def test_property_9_export_consistency_metadata_matches_effective():
    """
        Property 9: Export Consistency - Exported metadata matches effective values

        For any URL Node Map, each exported route's tags SHALL match
        get_effective_tags(), access_policy SHALL match
        get_effective_access_policy(), and rate_limit SHALL match
        get_effective_rate_limit() for that node.

        **Validates: Requirements 6.2, 6.3, 6.8**
    """
    for iteration in range(100):
        random.seed(iteration * 77771)

        node_map = URLNodeMap()

        # Generate random tree with metadata at various levels
        num_paths = random.randint(2, 10)
        paths = _generate_distinct_paths(num_paths, min_segments=1, max_segments=4)

        for path in paths:
            node = node_map.get_or_create_node(path)
            metadata = _generate_random_metadata()
            for key, value in metadata.items():
                node.set_metadata(key, value)

        # Also set metadata on some intermediate nodes for inheritance testing
        all_nodes = list(node_map.iterate_nodes())
        num_meta_nodes = random.randint(0, len(all_nodes))
        meta_indices = random.sample(range(len(all_nodes)), num_meta_nodes)
        for idx in meta_indices:
            node = all_nodes[idx]
            metadata = _generate_random_metadata()
            for key, value in metadata.items():
                node.set_metadata(key, value)

        # Attach handlers to create leaves
        non_leaf_nodes = [n for n in all_nodes if not n.is_leaf]
        if len(non_leaf_nodes) > 0:
            num_handlers = random.randint(1, max(1, len(non_leaf_nodes)))
            handler_nodes = random.sample(non_leaf_nodes, num_handlers)
            for node in handler_nodes:
                node.attach_handler("GET", _dummy_handler)

        # Export routes
        routes = node_map.export_routes()

        # Build a lookup from path to exported route
        route_by_path = {r["path"]: r for r in routes}

        # Verify each leaf node's effective metadata matches the export
        for node in node_map.iterate_nodes():
            if not node.is_leaf:
                continue

            if node.path not in route_by_path:
                errmsg = (
                    f"Iteration {iteration}: leaf path '{node.path}' not in export."
                )
                raise AssertionError(errmsg)

            route = route_by_path[node.path]

            # Check tags match get_effective_tags()
            expected_tags = node.get_effective_tags()
            if route["tags"] != expected_tags:
                errmsg = (
                    f"Iteration {iteration}: tags mismatch for '{node.path}'.\n"
                    f"  Expected (get_effective_tags): {expected_tags}\n"
                    f"  Got (export): {route['tags']}"
                )
                raise AssertionError(errmsg)

            # Check access_policy matches get_effective_access_policy()
            expected_policy = node.get_effective_access_policy()
            if expected_policy is not None:
                expected_policy_str = str(expected_policy)
            else:
                expected_policy_str = None
            if route["access_policy"] != expected_policy_str:
                errmsg = (
                    f"Iteration {iteration}: access_policy mismatch for '{node.path}'.\n"
                    f"  Expected (get_effective_access_policy): {expected_policy_str}\n"
                    f"  Got (export): {route['access_policy']}"
                )
                raise AssertionError(errmsg)

            # Check rate_limit matches get_effective_rate_limit()
            expected_limit = node.get_effective_rate_limit()
            if expected_limit is not None:
                expected_limit_str = str(expected_limit)
            else:
                expected_limit_str = None
            if route["rate_limit"] != expected_limit_str:
                errmsg = (
                    f"Iteration {iteration}: rate_limit mismatch for '{node.path}'.\n"
                    f"  Expected (get_effective_rate_limit): {expected_limit_str}\n"
                    f"  Got (export): {route['rate_limit']}"
                )
                raise AssertionError(errmsg)

    return
