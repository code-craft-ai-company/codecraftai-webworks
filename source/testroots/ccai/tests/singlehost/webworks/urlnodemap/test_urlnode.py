"""
    Tests for the URLNode class.
    
    This module contains unit tests for the URLNode class which represents
    a single node in the URL tree. Tests cover node creation, properties,
    child management, and parameter segment detection.
"""

from ccai.webworks.urlnodemap.urlnode import URLNode
from ccai.webworks.urlnodemap.exceptions import (
    NodeNotFoundError,
    NodeConflictError,
    PathConflictError,
)


# =============================================================================
# Unit Tests for URLNode Initialization
# =============================================================================

def test_urlnode_init_sets_segment():
    """
        Test that URLNode initialization sets the segment property.
    """
    node = URLNode(segment="api", path="/api", parent=None)
    
    if node.segment != "api":
        errmsg = f"Expected segment 'api', got '{node.segment}'"
        raise AssertionError(errmsg)
    
    return


def test_urlnode_init_sets_path():
    """
        Test that URLNode initialization sets the path property.
    """
    node = URLNode(segment="api", path="/api", parent=None)
    
    if node.path != "/api":
        errmsg = f"Expected path '/api', got '{node.path}'"
        raise AssertionError(errmsg)
    
    return


def test_urlnode_init_sets_parent():
    """
        Test that URLNode initialization sets the parent property.
    """
    parent = URLNode(segment="", path="/", parent=None)
    child = URLNode(segment="api", path="/api", parent=parent)
    
    if child.parent is not parent:
        errmsg = "Expected parent to be the parent node"
        raise AssertionError(errmsg)
    
    return


def test_urlnode_init_parent_none_for_root():
    """
        Test that root node has None parent.
    """
    root = URLNode(segment="", path="/", parent=None)
    
    if root.parent is not None:
        errmsg = "Expected root parent to be None"
        raise AssertionError(errmsg)
    
    return


def test_urlnode_init_children_empty():
    """
        Test that URLNode initialization creates empty children collection.
    """
    node = URLNode(segment="api", path="/api", parent=None)
    
    if len(node.children) != 0:
        errmsg = f"Expected empty children, got {len(node.children)} children"
        raise AssertionError(errmsg)
    
    return


# =============================================================================
# Unit Tests for Parameter Segment Detection
# =============================================================================

def test_urlnode_is_parameter_true_for_parameter_segment():
    """
        Test that is_parameter returns True for parameter segments.
        
        Validates: Requirements 7.2
    """
    node = URLNode(segment="{user_id}", path="/api/{user_id}", parent=None)
    
    if node.is_parameter is not True:
        errmsg = f"Expected is_parameter True, got {node.is_parameter}"
        raise AssertionError(errmsg)
    
    return


def test_urlnode_is_parameter_false_for_literal_segment():
    """
        Test that is_parameter returns False for literal segments.
        
        Validates: Requirements 7.2
    """
    node = URLNode(segment="users", path="/api/users", parent=None)
    
    if node.is_parameter is not False:
        errmsg = f"Expected is_parameter False, got {node.is_parameter}"
        raise AssertionError(errmsg)
    
    return


def test_urlnode_parameter_name_for_parameter_segment():
    """
        Test that parameter_name returns the name for parameter segments.
        
        Validates: Requirements 7.3
    """
    node = URLNode(segment="{user_id}", path="/api/{user_id}", parent=None)
    
    if node.parameter_name != "user_id":
        errmsg = f"Expected parameter_name 'user_id', got '{node.parameter_name}'"
        raise AssertionError(errmsg)
    
    return


def test_urlnode_parameter_name_none_for_literal_segment():
    """
        Test that parameter_name returns None for literal segments.
        
        Validates: Requirements 7.3
    """
    node = URLNode(segment="users", path="/api/users", parent=None)
    
    if node.parameter_name is not None:
        errmsg = f"Expected parameter_name None, got '{node.parameter_name}'"
        raise AssertionError(errmsg)
    
    return


def test_urlnode_parameter_name_simple():
    """
        Test parameter_name with simple single-character name.
    """
    node = URLNode(segment="{id}", path="/api/{id}", parent=None)
    
    if node.parameter_name != "id":
        errmsg = f"Expected parameter_name 'id', got '{node.parameter_name}'"
        raise AssertionError(errmsg)
    
    return


def test_urlnode_parameter_name_with_underscores():
    """
        Test parameter_name with underscores in name.
    """
    node = URLNode(segment="{user_profile_id}", path="/api/{user_profile_id}", parent=None)
    
    if node.parameter_name != "user_profile_id":
        errmsg = f"Expected parameter_name 'user_profile_id', got '{node.parameter_name}'"
        raise AssertionError(errmsg)
    
    return


# =============================================================================
# Unit Tests for get_child Method
# =============================================================================

def test_urlnode_get_child_returns_existing_child():
    """
        Test that get_child returns an existing child node.
        
        Validates: Requirements 2.7
    """
    parent = URLNode(segment="", path="/", parent=None)
    child = parent.add_child("api")
    
    result = parent.get_child("api")
    
    if result is not child:
        errmsg = "Expected get_child to return the added child"
        raise AssertionError(errmsg)
    
    return


def test_urlnode_get_child_raises_for_nonexistent():
    """
        Test that get_child raises NodeNotFoundError for nonexistent child.
        
        Validates: Requirements 2.7
    """
    parent = URLNode(segment="", path="/", parent=None)
    
    try:
        parent.get_child("nonexistent")
        errmsg = "Expected NodeNotFoundError to be raised"
        raise AssertionError(errmsg)
    except NodeNotFoundError as exc:
        if exc.path != "/nonexistent":
            errmsg = f"Expected path '/nonexistent', got '{exc.path}'"
            raise AssertionError(errmsg)
    
    return


def test_urlnode_get_child_raises_with_correct_path():
    """
        Test that get_child raises NodeNotFoundError with correct path.
    """
    root = URLNode(segment="", path="/", parent=None)
    api = root.add_child("api")
    
    try:
        api.get_child("nonexistent")
        errmsg = "Expected NodeNotFoundError to be raised"
        raise AssertionError(errmsg)
    except NodeNotFoundError as exc:
        if exc.path != "/api/nonexistent":
            errmsg = f"Expected path '/api/nonexistent', got '{exc.path}'"
            raise AssertionError(errmsg)
    
    return


def test_urlnode_get_child_multiple_children():
    """
        Test get_child with multiple children.
    """
    parent = URLNode(segment="", path="/", parent=None)
    child1 = parent.add_child("api")
    child2 = parent.add_child("docs")
    child3 = parent.add_child("static")
    
    if parent.get_child("api") is not child1:
        errmsg = "Expected get_child('api') to return child1"
        raise AssertionError(errmsg)
    
    if parent.get_child("docs") is not child2:
        errmsg = "Expected get_child('docs') to return child2"
        raise AssertionError(errmsg)
    
    if parent.get_child("static") is not child3:
        errmsg = "Expected get_child('static') to return child3"
        raise AssertionError(errmsg)
    
    return


# =============================================================================
# Unit Tests for add_child Method
# =============================================================================

def test_urlnode_add_child_creates_child():
    """
        Test that add_child creates a new child node.
        
        Validates: Requirements 2.8
    """
    parent = URLNode(segment="", path="/", parent=None)
    
    child = parent.add_child("api")
    
    if child is None:
        errmsg = "Expected add_child to return a child node"
        raise AssertionError(errmsg)
    
    return


def test_urlnode_add_child_sets_segment():
    """
        Test that add_child sets the correct segment on child.
    """
    parent = URLNode(segment="", path="/", parent=None)
    
    child = parent.add_child("api")
    
    if child.segment != "api":
        errmsg = f"Expected segment 'api', got '{child.segment}'"
        raise AssertionError(errmsg)
    
    return


def test_urlnode_add_child_sets_path_from_root():
    """
        Test that add_child sets the correct path from root.
        
        Validates: Requirements 1.6
    """
    root = URLNode(segment="", path="/", parent=None)
    
    child = root.add_child("api")
    
    if child.path != "/api":
        errmsg = f"Expected path '/api', got '{child.path}'"
        raise AssertionError(errmsg)
    
    return


def test_urlnode_add_child_sets_path_from_parent():
    """
        Test that add_child sets the correct path from non-root parent.
        
        Validates: Requirements 1.6
    """
    root = URLNode(segment="", path="/", parent=None)
    api = root.add_child("api")
    
    v1 = api.add_child("v1")
    
    if v1.path != "/api/v1":
        errmsg = f"Expected path '/api/v1', got '{v1.path}'"
        raise AssertionError(errmsg)
    
    return


def test_urlnode_add_child_sets_parent_reference():
    """
        Test that add_child sets the parent reference on child.
        
        Validates: Requirements 1.6
    """
    parent = URLNode(segment="", path="/", parent=None)
    
    child = parent.add_child("api")
    
    if child.parent is not parent:
        errmsg = "Expected child.parent to be the parent node"
        raise AssertionError(errmsg)
    
    return


def test_urlnode_add_child_adds_to_children_collection():
    """
        Test that add_child adds the child to the children collection.
    """
    parent = URLNode(segment="", path="/", parent=None)
    
    child = parent.add_child("api")
    
    if "api" not in parent.children:
        errmsg = "Expected 'api' to be in parent.children"
        raise AssertionError(errmsg)
    
    if parent.children["api"] is not child:
        errmsg = "Expected parent.children['api'] to be the child"
        raise AssertionError(errmsg)
    
    return


def test_urlnode_add_child_with_metadata():
    """
        Test that add_child applies initial metadata.
    """
    parent = URLNode(segment="", path="/", parent=None)
    
    child = parent.add_child("api", version="v1", tags=["public"])
    
    if child._metadata.get("version") != "v1":
        errmsg = f"Expected version 'v1', got '{child._metadata.get('version')}'"
        raise AssertionError(errmsg)
    
    if child._metadata.get("tags") != ["public"]:
        errmsg = f"Expected tags ['public'], got '{child._metadata.get('tags')}'"
        raise AssertionError(errmsg)
    
    return


def test_urlnode_add_child_raises_for_duplicate():
    """
        Test that add_child raises NodeConflictError for duplicate segment.
        
        Validates: Requirements 1.8
    """
    parent = URLNode(segment="", path="/", parent=None)
    parent.add_child("api")
    
    try:
        parent.add_child("api")
        errmsg = "Expected NodeConflictError to be raised"
        raise AssertionError(errmsg)
    except NodeConflictError as exc:
        if exc.path != "/api":
            errmsg = f"Expected path '/api', got '{exc.path}'"
            raise AssertionError(errmsg)
    
    return


def test_urlnode_add_child_raises_for_parameter_literal_conflict():
    """
        Test that add_child raises PathConflictError when adding parameter
        after literal segment exists.
        
        Validates: Requirements 7.7
    """
    parent = URLNode(segment="", path="/", parent=None)
    parent.add_child("users")
    
    try:
        parent.add_child("{id}")
        errmsg = "Expected PathConflictError to be raised"
        raise AssertionError(errmsg)
    except PathConflictError as exc:
        if exc.parameter_segment != "{id}":
            errmsg = f"Expected parameter_segment '{{id}}', got '{exc.parameter_segment}'"
            raise AssertionError(errmsg)
        if exc.literal_segment != "users":
            errmsg = f"Expected literal_segment 'users', got '{exc.literal_segment}'"
            raise AssertionError(errmsg)
    
    return


def test_urlnode_add_child_raises_for_literal_parameter_conflict():
    """
        Test that add_child raises PathConflictError when adding literal
        after parameter segment exists.
        
        Validates: Requirements 7.7
    """
    parent = URLNode(segment="", path="/", parent=None)
    parent.add_child("{id}")
    
    try:
        parent.add_child("users")
        errmsg = "Expected PathConflictError to be raised"
        raise AssertionError(errmsg)
    except PathConflictError as exc:
        if exc.parameter_segment != "{id}":
            errmsg = f"Expected parameter_segment '{{id}}', got '{exc.parameter_segment}'"
            raise AssertionError(errmsg)
        if exc.literal_segment != "users":
            errmsg = f"Expected literal_segment 'users', got '{exc.literal_segment}'"
            raise AssertionError(errmsg)
    
    return


def test_urlnode_add_child_allows_multiple_literals():
    """
        Test that add_child allows multiple literal children.
    """
    parent = URLNode(segment="", path="/", parent=None)
    
    parent.add_child("api")
    parent.add_child("docs")
    parent.add_child("static")
    
    if len(parent.children) != 3:
        errmsg = f"Expected 3 children, got {len(parent.children)}"
        raise AssertionError(errmsg)
    
    return


def test_urlnode_add_child_parameter_segment():
    """
        Test that add_child correctly handles parameter segments.
        
        Validates: Requirements 7.2, 7.3
    """
    parent = URLNode(segment="", path="/", parent=None)
    
    child = parent.add_child("{user_id}")
    
    if child.is_parameter is not True:
        errmsg = f"Expected is_parameter True, got {child.is_parameter}"
        raise AssertionError(errmsg)
    
    if child.parameter_name != "user_id":
        errmsg = f"Expected parameter_name 'user_id', got '{child.parameter_name}'"
        raise AssertionError(errmsg)
    
    return


# =============================================================================
# Unit Tests for children Property
# =============================================================================

def test_urlnode_children_returns_immutable_view():
    """
        Test that children property returns an immutable view.
    """
    parent = URLNode(segment="", path="/", parent=None)
    parent.add_child("api")
    
    children = parent.children
    
    # Attempting to modify should raise an error
    try:
        children["new"] = URLNode(segment="new", path="/new", parent=None)
        errmsg = "Expected TypeError when modifying immutable children"
        raise AssertionError(errmsg)
    except TypeError:
        pass  # Expected behavior
    
    return


def test_urlnode_children_reflects_added_children():
    """
        Test that children property reflects added children.
    """
    parent = URLNode(segment="", path="/", parent=None)
    
    parent.add_child("api")
    parent.add_child("docs")
    
    if "api" not in parent.children:
        errmsg = "Expected 'api' in children"
        raise AssertionError(errmsg)
    
    if "docs" not in parent.children:
        errmsg = "Expected 'docs' in children"
        raise AssertionError(errmsg)
    
    return


# =============================================================================
# Unit Tests for Deep Path Construction
# =============================================================================

def test_urlnode_deep_path_construction():
    """
        Test constructing a deep path through multiple add_child calls.
        
        Validates: Requirements 1.3, 1.6
    """
    root = URLNode(segment="", path="/", parent=None)
    api = root.add_child("api")
    v1 = api.add_child("v1")
    users = v1.add_child("users")
    user_id = users.add_child("{user_id}")
    
    if user_id.path != "/api/v1/users/{user_id}":
        errmsg = f"Expected path '/api/v1/users/{{user_id}}', got '{user_id.path}'"
        raise AssertionError(errmsg)
    
    # Verify parent chain
    if user_id.parent is not users:
        errmsg = "Expected user_id.parent to be users"
        raise AssertionError(errmsg)
    
    if users.parent is not v1:
        errmsg = "Expected users.parent to be v1"
        raise AssertionError(errmsg)
    
    if v1.parent is not api:
        errmsg = "Expected v1.parent to be api"
        raise AssertionError(errmsg)
    
    if api.parent is not root:
        errmsg = "Expected api.parent to be root"
        raise AssertionError(errmsg)
    
    return


def test_urlnode_sibling_paths_independent():
    """
        Test that sibling nodes have independent paths.
    """
    root = URLNode(segment="", path="/", parent=None)
    api = root.add_child("api")
    docs = root.add_child("docs")
    
    api_v1 = api.add_child("v1")
    docs_v1 = docs.add_child("v1")
    
    if api_v1.path != "/api/v1":
        errmsg = f"Expected api_v1.path '/api/v1', got '{api_v1.path}'"
        raise AssertionError(errmsg)
    
    if docs_v1.path != "/docs/v1":
        errmsg = f"Expected docs_v1.path '/docs/v1', got '{docs_v1.path}'"
        raise AssertionError(errmsg)
    
    return



# =============================================================================
# Property-Based Tests for Parent-Child Consistency
# =============================================================================

import random
import string


def _generate_valid_segment() -> str:
    """
        Generate a valid path segment for testing.
        
        Segments can be:
        - Literal segments: alphanumeric with underscores and hyphens
        - Parameter segments: {param_name}
        
        :returns: A valid segment string.
    """
    # 80% chance of literal segment, 20% chance of parameter segment
    if random.random() < 0.8:
        # Generate literal segment
        length = random.randint(1, 15)
        chars = string.ascii_lowercase + string.digits + "_-"
        # First character must be a letter
        first_char = random.choice(string.ascii_lowercase)
        rest = "".join(random.choice(chars) for _ in range(length - 1))
        return first_char + rest
    else:
        # Generate parameter segment
        length = random.randint(1, 12)
        chars = string.ascii_lowercase + "_"
        first_char = random.choice(string.ascii_lowercase)
        rest = "".join(random.choice(chars) for _ in range(length - 1))
        return "{" + first_char + rest + "}"


def _build_random_tree(max_depth: int = 4, max_children_per_node: int = 4) -> URLNode:
    """
        Build a random URL tree for property testing.
        
        :param max_depth: Maximum depth of the tree.
        :param max_children_per_node: Maximum number of children per node.
        
        :returns: The root URLNode of the generated tree.
    """
    root = URLNode(segment="", path="/", parent=None)
    
    def add_children_recursively(node: URLNode, current_depth: int):
        if current_depth >= max_depth:
            return
        
        # Decide how many children to add (0 to max_children_per_node)
        num_children = random.randint(0, max_children_per_node)
        
        # Track if we've added a parameter segment at this level
        has_parameter = False
        
        for _ in range(num_children):
            segment = _generate_valid_segment()
            
            # Skip if this would create a parameter/literal conflict
            is_param = segment.startswith("{") and segment.endswith("}")
            
            if is_param and has_parameter:
                # Already have a parameter at this level, skip
                continue
            
            if is_param:
                # Check if any literal children exist
                has_literal = any(not c.is_parameter for c in node.children.values())
                if has_literal:
                    continue
                has_parameter = True
            else:
                # Check if a parameter child exists
                has_param_child = any(c.is_parameter for c in node.children.values())
                if has_param_child:
                    continue
            
            # Check for duplicate segment
            if segment in node.children:
                continue
            
            try:
                child = node.add_child(segment)
                add_children_recursively(child, current_depth + 1)
            except (NodeConflictError, PathConflictError):
                # Skip on conflict
                pass
    
    add_children_recursively(root, 0)
    return root


def _collect_all_nodes(root: URLNode) -> list:
    """
        Collect all nodes in the tree using depth-first traversal.
        
        :param root: The root node of the tree.
        
        :returns: List of all URLNode instances in the tree.
    """
    nodes = [root]
    
    def collect_descendants(node: URLNode):
        for child in node.children.values():
            nodes.append(child)
            collect_descendants(child)
    
    collect_descendants(root)
    return nodes


def test_property_parent_child_consistency():
    """
        Property 4: Parent-Child Consistency
        
        *For any* node in the tree (except root), the node's parent's children
        collection SHALL contain the node, and the node's path SHALL equal
        the parent's path plus "/" plus the node's segment.
        
        **Validates: Requirements 1.6**
        
        This property test generates random tree structures and verifies that
        the parent-child relationship is consistent for all non-root nodes.
    """
    num_iterations = 100
    
    for iteration in range(num_iterations):
        # Set a different seed for each iteration for reproducibility
        random.seed(iteration * 12345)
        
        # Build a random tree
        root = _build_random_tree(max_depth=4, max_children_per_node=4)
        
        # Collect all nodes in the tree
        all_nodes = _collect_all_nodes(root)
        
        # Verify parent-child consistency for all non-root nodes
        for node in all_nodes:
            if node.parent is None:
                # Root node - skip parent-child checks
                if node.path != "/":
                    errmsg = (
                        f"Iteration {iteration}: Root node should have path '/', "
                        f"got '{node.path}'"
                    )
                    raise AssertionError(errmsg)
                continue
            
            # Property 4a: Parent's children collection SHALL contain the node
            parent = node.parent
            found_in_parent = False
            for child_segment, child_node in parent.children.items():
                if child_node is node:
                    found_in_parent = True
                    # Also verify the segment key matches
                    if child_segment != node.segment:
                        errmsg = (
                            f"Iteration {iteration}: Node at '{node.path}' has segment "
                            f"'{node.segment}' but is stored under key '{child_segment}' "
                            f"in parent's children"
                        )
                        raise AssertionError(errmsg)
                    break
            
            if not found_in_parent:
                errmsg = (
                    f"Iteration {iteration}: Node at '{node.path}' is not found in "
                    f"parent's children collection (parent path: '{parent.path}')"
                )
                raise AssertionError(errmsg)
            
            # Property 4b: Node's path SHALL equal parent's path + "/" + node's segment
            if parent.path == "/":
                expected_path = "/" + node.segment
            else:
                expected_path = parent.path + "/" + node.segment
            
            if node.path != expected_path:
                errmsg = (
                    f"Iteration {iteration}: Node path mismatch. "
                    f"Expected '{expected_path}' (parent.path='{parent.path}' + '/' + "
                    f"segment='{node.segment}'), got '{node.path}'"
                )
                raise AssertionError(errmsg)
    
    return


def test_property_parent_child_consistency_single_chain():
    """
        Property 4: Parent-Child Consistency - Single Chain Variant
        
        Tests parent-child consistency on a single deep chain of nodes.
        
        **Validates: Requirements 1.6**
    """
    num_iterations = 100
    
    for iteration in range(num_iterations):
        random.seed(iteration * 54321)
        
        # Build a single chain of random depth
        depth = random.randint(1, 8)
        
        root = URLNode(segment="", path="/", parent=None)
        current = root
        
        for _ in range(depth):
            segment = _generate_valid_segment()
            # Ensure we don't create parameter segments to avoid conflicts
            while segment.startswith("{"):
                segment = _generate_valid_segment()
            
            child = current.add_child(segment)
            current = child
        
        # Verify the chain from leaf to root
        node = current
        while node.parent is not None:
            parent = node.parent
            
            # Verify node is in parent's children
            if node.segment not in parent.children:
                errmsg = (
                    f"Iteration {iteration}: Node segment '{node.segment}' not found "
                    f"in parent's children keys"
                )
                raise AssertionError(errmsg)
            
            if parent.children[node.segment] is not node:
                errmsg = (
                    f"Iteration {iteration}: Parent's children['{node.segment}'] does not "
                    f"reference the correct node"
                )
                raise AssertionError(errmsg)
            
            # Verify path construction
            if parent.path == "/":
                expected_path = "/" + node.segment
            else:
                expected_path = parent.path + "/" + node.segment
            
            if node.path != expected_path:
                errmsg = (
                    f"Iteration {iteration}: Path mismatch. Expected '{expected_path}', "
                    f"got '{node.path}'"
                )
                raise AssertionError(errmsg)
            
            node = parent
    
    return


def test_property_parent_child_consistency_wide_tree():
    """
        Property 4: Parent-Child Consistency - Wide Tree Variant
        
        Tests parent-child consistency on trees with many children per node.
        
        **Validates: Requirements 1.6**
    """
    num_iterations = 100
    
    for iteration in range(num_iterations):
        random.seed(iteration * 98765)
        
        root = URLNode(segment="", path="/", parent=None)
        
        # Add many children to root
        num_children = random.randint(1, 10)
        children = []
        
        for i in range(num_children):
            segment = f"segment{i}"
            child = root.add_child(segment)
            children.append(child)
            
            # Add some grandchildren
            num_grandchildren = random.randint(0, 5)
            for j in range(num_grandchildren):
                grandchild_segment = f"sub{j}"
                child.add_child(grandchild_segment)
        
        # Verify all nodes
        all_nodes = _collect_all_nodes(root)
        
        for node in all_nodes:
            if node.parent is None:
                continue
            
            parent = node.parent
            
            # Verify node is in parent's children
            if node.segment not in parent.children:
                errmsg = (
                    f"Iteration {iteration}: Segment '{node.segment}' not in parent's "
                    f"children at path '{parent.path}'"
                )
                raise AssertionError(errmsg)
            
            if parent.children[node.segment] is not node:
                errmsg = (
                    f"Iteration {iteration}: Parent's children reference mismatch for "
                    f"segment '{node.segment}'"
                )
                raise AssertionError(errmsg)
            
            # Verify path
            if parent.path == "/":
                expected_path = "/" + node.segment
            else:
                expected_path = parent.path + "/" + node.segment
            
            if node.path != expected_path:
                errmsg = (
                    f"Iteration {iteration}: Path mismatch for node. "
                    f"Expected '{expected_path}', got '{node.path}'"
                )
                raise AssertionError(errmsg)
    
    return


# =============================================================================
# Unit Tests for Metadata Methods
# =============================================================================

def test_urlnode_metadata_property_returns_copy():
    """
        Test that metadata property returns a copy of the metadata dictionary.
        
        Validates: Requirements 3.5
    """
    node = URLNode(segment="api", path="/api", parent=None)
    node._metadata["key1"] = "value1"
    node._metadata["key2"] = "value2"
    
    metadata = node.metadata
    
    # Verify it contains the expected values
    if metadata.get("key1") != "value1":
        errmsg = f"Expected metadata['key1'] = 'value1', got '{metadata.get('key1')}'"
        raise AssertionError(errmsg)
    
    if metadata.get("key2") != "value2":
        errmsg = f"Expected metadata['key2'] = 'value2', got '{metadata.get('key2')}'"
        raise AssertionError(errmsg)
    
    return


def test_urlnode_metadata_property_returns_independent_copy():
    """
        Test that modifying the returned metadata does not affect the node.
        
        Validates: Requirements 3.5
    """
    node = URLNode(segment="api", path="/api", parent=None)
    node._metadata["key1"] = "value1"
    
    metadata = node.metadata
    metadata["key1"] = "modified"
    metadata["new_key"] = "new_value"
    
    # Verify the node's internal metadata is unchanged
    if node._metadata.get("key1") != "value1":
        errmsg = f"Expected node._metadata['key1'] = 'value1', got '{node._metadata.get('key1')}'"
        raise AssertionError(errmsg)
    
    if "new_key" in node._metadata:
        errmsg = "Expected 'new_key' not to be in node._metadata"
        raise AssertionError(errmsg)
    
    return


def test_urlnode_metadata_property_empty_initially():
    """
        Test that metadata property returns empty dict for new node.
    """
    node = URLNode(segment="api", path="/api", parent=None)
    
    metadata = node.metadata
    
    if len(metadata) != 0:
        errmsg = f"Expected empty metadata, got {len(metadata)} items"
        raise AssertionError(errmsg)
    
    return


def test_urlnode_get_metadata_returns_value():
    """
        Test that get_metadata returns the value for an existing key.
        
        Validates: Requirements 3.4
    """
    node = URLNode(segment="api", path="/api", parent=None)
    node._metadata["access_policy"] = "admin"
    
    result = node.get_metadata("access_policy")
    
    if result != "admin":
        errmsg = f"Expected 'admin', got '{result}'"
        raise AssertionError(errmsg)
    
    return


def test_urlnode_get_metadata_returns_none_for_missing_key():
    """
        Test that get_metadata returns None for a non-existent key.
        
        Validates: Requirements 3.4
    """
    node = URLNode(segment="api", path="/api", parent=None)
    
    result = node.get_metadata("nonexistent")
    
    if result is not None:
        errmsg = f"Expected None, got '{result}'"
        raise AssertionError(errmsg)
    
    return


def test_urlnode_get_metadata_various_types():
    """
        Test that get_metadata works with various value types.
        
        Validates: Requirements 3.1, 3.4
    """
    node = URLNode(segment="api", path="/api", parent=None)
    node._metadata["string_val"] = "test"
    node._metadata["int_val"] = 42
    node._metadata["list_val"] = ["a", "b", "c"]
    node._metadata["dict_val"] = {"nested": "value"}
    node._metadata["none_val"] = None
    node._metadata["bool_val"] = True
    
    if node.get_metadata("string_val") != "test":
        errmsg = f"Expected 'test', got '{node.get_metadata('string_val')}'"
        raise AssertionError(errmsg)
    
    if node.get_metadata("int_val") != 42:
        errmsg = f"Expected 42, got '{node.get_metadata('int_val')}'"
        raise AssertionError(errmsg)
    
    if node.get_metadata("list_val") != ["a", "b", "c"]:
        errmsg = f"Expected ['a', 'b', 'c'], got '{node.get_metadata('list_val')}'"
        raise AssertionError(errmsg)
    
    if node.get_metadata("dict_val") != {"nested": "value"}:
        errmsg = f"Expected {{'nested': 'value'}}, got '{node.get_metadata('dict_val')}'"
        raise AssertionError(errmsg)
    
    # Note: None is a valid value, distinct from key not existing
    if node.get_metadata("none_val") is not None:
        errmsg = f"Expected None, got '{node.get_metadata('none_val')}'"
        raise AssertionError(errmsg)
    
    if node.get_metadata("bool_val") is not True:
        errmsg = f"Expected True, got '{node.get_metadata('bool_val')}'"
        raise AssertionError(errmsg)
    
    return


def test_urlnode_set_metadata_sets_value():
    """
        Test that set_metadata sets a new metadata value.
        
        Validates: Requirements 3.4
    """
    node = URLNode(segment="api", path="/api", parent=None)
    
    node.set_metadata("rate_limit", 100)
    
    if node._metadata.get("rate_limit") != 100:
        errmsg = f"Expected 100, got '{node._metadata.get('rate_limit')}'"
        raise AssertionError(errmsg)
    
    return


def test_urlnode_set_metadata_overwrites_existing():
    """
        Test that set_metadata overwrites an existing value.
        
        Validates: Requirements 3.4
    """
    node = URLNode(segment="api", path="/api", parent=None)
    node._metadata["version"] = "v1"
    
    node.set_metadata("version", "v2")
    
    if node._metadata.get("version") != "v2":
        errmsg = f"Expected 'v2', got '{node._metadata.get('version')}'"
        raise AssertionError(errmsg)
    
    return


def test_urlnode_set_metadata_various_types():
    """
        Test that set_metadata works with various value types.
        
        Validates: Requirements 3.1, 3.4
    """
    node = URLNode(segment="api", path="/api", parent=None)
    
    node.set_metadata("string_val", "test")
    node.set_metadata("int_val", 42)
    node.set_metadata("list_val", ["a", "b", "c"])
    node.set_metadata("dict_val", {"nested": "value"})
    node.set_metadata("none_val", None)
    node.set_metadata("bool_val", True)
    
    if node._metadata.get("string_val") != "test":
        errmsg = f"Expected 'test', got '{node._metadata.get('string_val')}'"
        raise AssertionError(errmsg)
    
    if node._metadata.get("int_val") != 42:
        errmsg = f"Expected 42, got '{node._metadata.get('int_val')}'"
        raise AssertionError(errmsg)
    
    if node._metadata.get("list_val") != ["a", "b", "c"]:
        errmsg = f"Expected ['a', 'b', 'c'], got '{node._metadata.get('list_val')}'"
        raise AssertionError(errmsg)
    
    if node._metadata.get("dict_val") != {"nested": "value"}:
        errmsg = f"Expected {{'nested': 'value'}}, got '{node._metadata.get('dict_val')}'"
        raise AssertionError(errmsg)
    
    if node._metadata.get("none_val") is not None:
        errmsg = f"Expected None, got '{node._metadata.get('none_val')}'"
        raise AssertionError(errmsg)
    
    if node._metadata.get("bool_val") is not True:
        errmsg = f"Expected True, got '{node._metadata.get('bool_val')}'"
        raise AssertionError(errmsg)
    
    return


def test_urlnode_get_set_metadata_roundtrip():
    """
        Test that get_metadata returns what was set with set_metadata.
        
        Validates: Requirements 3.4
    """
    node = URLNode(segment="api", path="/api", parent=None)
    
    node.set_metadata("tags", ["public", "v1"])
    result = node.get_metadata("tags")
    
    if result != ["public", "v1"]:
        errmsg = f"Expected ['public', 'v1'], got '{result}'"
        raise AssertionError(errmsg)
    
    return


def test_urlnode_metadata_property_reflects_set_metadata():
    """
        Test that metadata property reflects values set via set_metadata.
        
        Validates: Requirements 3.4, 3.5
    """
    node = URLNode(segment="api", path="/api", parent=None)
    
    node.set_metadata("access_policy", "admin")
    node.set_metadata("rate_limit", 50)
    
    metadata = node.metadata
    
    if metadata.get("access_policy") != "admin":
        errmsg = f"Expected 'admin', got '{metadata.get('access_policy')}'"
        raise AssertionError(errmsg)
    
    if metadata.get("rate_limit") != 50:
        errmsg = f"Expected 50, got '{metadata.get('rate_limit')}'"
        raise AssertionError(errmsg)
    
    return


def test_urlnode_metadata_with_add_child():
    """
        Test that metadata set via add_child is accessible via get_metadata.
        
        Validates: Requirements 3.4
    """
    parent = URLNode(segment="", path="/", parent=None)
    child = parent.add_child("api", version="v1", tags=["public"])
    
    if child.get_metadata("version") != "v1":
        errmsg = f"Expected 'v1', got '{child.get_metadata('version')}'"
        raise AssertionError(errmsg)
    
    if child.get_metadata("tags") != ["public"]:
        errmsg = f"Expected ['public'], got '{child.get_metadata('tags')}'"
        raise AssertionError(errmsg)
    
    return


def test_urlnode_metadata_empty_string_key():
    """
        Test that metadata works with empty string key.
    """
    node = URLNode(segment="api", path="/api", parent=None)
    
    node.set_metadata("", "empty_key_value")
    
    if node.get_metadata("") != "empty_key_value":
        errmsg = f"Expected 'empty_key_value', got '{node.get_metadata('')}'"
        raise AssertionError(errmsg)
    
    return


def test_urlnode_metadata_special_characters_in_key():
    """
        Test that metadata works with special characters in key.
    """
    node = URLNode(segment="api", path="/api", parent=None)
    
    node.set_metadata("key.with.dots", "value1")
    node.set_metadata("key-with-dashes", "value2")
    node.set_metadata("key_with_underscores", "value3")
    
    if node.get_metadata("key.with.dots") != "value1":
        errmsg = f"Expected 'value1', got '{node.get_metadata('key.with.dots')}'"
        raise AssertionError(errmsg)
    
    if node.get_metadata("key-with-dashes") != "value2":
        errmsg = f"Expected 'value2', got '{node.get_metadata('key-with-dashes')}'"
        raise AssertionError(errmsg)
    
    if node.get_metadata("key_with_underscores") != "value3":
        errmsg = f"Expected 'value3', got '{node.get_metadata('key_with_underscores')}'"
        raise AssertionError(errmsg)
    
    return


# =============================================================================
# Unit Tests for is_leaf Property
# =============================================================================

def test_urlnode_is_leaf_false_when_no_handlers():
    """
        Test that is_leaf returns False when no handlers are attached.
        
        Validates: Requirements 3.6
    """
    node = URLNode(segment="api", path="/api", parent=None)
    
    if node.is_leaf is not False:
        errmsg = f"Expected is_leaf False, got {node.is_leaf}"
        raise AssertionError(errmsg)
    
    return


def test_urlnode_is_leaf_true_when_handler_attached():
    """
        Test that is_leaf returns True when a handler is attached.
        
        Validates: Requirements 3.6
    """
    node = URLNode(segment="api", path="/api", parent=None)
    
    def handler():
        pass
    
    node.attach_handler("GET", handler)
    
    if node.is_leaf is not True:
        errmsg = f"Expected is_leaf True, got {node.is_leaf}"
        raise AssertionError(errmsg)
    
    return


def test_urlnode_is_leaf_true_with_multiple_handlers():
    """
        Test that is_leaf returns True when multiple handlers are attached.
        
        Validates: Requirements 3.6, 3.7
    """
    node = URLNode(segment="api", path="/api", parent=None)
    
    def get_handler():
        pass
    
    def post_handler():
        pass
    
    node.attach_handler("GET", get_handler)
    node.attach_handler("POST", post_handler)
    
    if node.is_leaf is not True:
        errmsg = f"Expected is_leaf True, got {node.is_leaf}"
        raise AssertionError(errmsg)
    
    return


# =============================================================================
# Unit Tests for attach_handler Method
# =============================================================================

def test_urlnode_attach_handler_stores_handler():
    """
        Test that attach_handler stores the handler for the method.
        
        Validates: Requirements 3.6
    """
    node = URLNode(segment="api", path="/api", parent=None)
    
    def handler():
        return "response"
    
    node.attach_handler("GET", handler)
    
    if node._handlers.get("GET") is not handler:
        errmsg = "Expected handler to be stored in _handlers"
        raise AssertionError(errmsg)
    
    return


def test_urlnode_attach_handler_normalizes_method_to_uppercase():
    """
        Test that attach_handler normalizes method name to uppercase.
        
        Validates: Requirements 3.6
    """
    node = URLNode(segment="api", path="/api", parent=None)
    
    def handler():
        pass
    
    node.attach_handler("get", handler)
    
    if "GET" not in node._handlers:
        errmsg = "Expected 'GET' (uppercase) in _handlers"
        raise AssertionError(errmsg)
    
    if "get" in node._handlers:
        errmsg = "Expected 'get' (lowercase) not in _handlers"
        raise AssertionError(errmsg)
    
    return


def test_urlnode_attach_handler_multiple_methods():
    """
        Test that attach_handler allows multiple methods on same node.
        
        Validates: Requirements 3.7
    """
    node = URLNode(segment="api", path="/api", parent=None)
    
    def get_handler():
        return "get"
    
    def post_handler():
        return "post"
    
    def put_handler():
        return "put"
    
    def delete_handler():
        return "delete"
    
    node.attach_handler("GET", get_handler)
    node.attach_handler("POST", post_handler)
    node.attach_handler("PUT", put_handler)
    node.attach_handler("DELETE", delete_handler)
    
    if len(node._handlers) != 4:
        errmsg = f"Expected 4 handlers, got {len(node._handlers)}"
        raise AssertionError(errmsg)
    
    return


def test_urlnode_attach_handler_raises_for_duplicate_method():
    """
        Test that attach_handler raises HandlerConflictError for duplicate method.
        
        Validates: Requirements 3.6
    """
    from ccai.webworks.urlnodemap.exceptions import HandlerConflictError
    
    node = URLNode(segment="api", path="/api", parent=None)
    
    def handler1():
        return "first"
    
    def handler2():
        return "second"
    
    node.attach_handler("GET", handler1)
    
    try:
        node.attach_handler("GET", handler2)
        errmsg = "Expected HandlerConflictError to be raised"
        raise AssertionError(errmsg)
    except HandlerConflictError as exc:
        if exc.path != "/api":
            errmsg = f"Expected path '/api', got '{exc.path}'"
            raise AssertionError(errmsg)
        if exc.method != "GET":
            errmsg = f"Expected method 'GET', got '{exc.method}'"
            raise AssertionError(errmsg)
        if exc.existing_handler is not handler1:
            errmsg = "Expected existing_handler to be handler1"
            raise AssertionError(errmsg)
    
    return


def test_urlnode_attach_handler_raises_for_duplicate_case_insensitive():
    """
        Test that attach_handler raises HandlerConflictError for same method
        with different case.
        
        Validates: Requirements 3.6
    """
    from ccai.webworks.urlnodemap.exceptions import HandlerConflictError
    
    node = URLNode(segment="api", path="/api", parent=None)
    
    def handler1():
        pass
    
    def handler2():
        pass
    
    node.attach_handler("GET", handler1)
    
    try:
        node.attach_handler("get", handler2)
        errmsg = "Expected HandlerConflictError to be raised"
        raise AssertionError(errmsg)
    except HandlerConflictError as exc:
        if exc.method != "GET":
            errmsg = f"Expected method 'GET', got '{exc.method}'"
            raise AssertionError(errmsg)
    
    return


def test_urlnode_attach_handler_with_lambda():
    """
        Test that attach_handler works with lambda functions.
    """
    node = URLNode(segment="api", path="/api", parent=None)
    
    handler = lambda: "lambda response"
    
    node.attach_handler("GET", handler)
    
    if node._handlers.get("GET") is not handler:
        errmsg = "Expected lambda handler to be stored"
        raise AssertionError(errmsg)
    
    return


def test_urlnode_attach_handler_with_class_method():
    """
        Test that attach_handler works with class methods.
    """
    class Controller:
        def handle_get(self):
            return "class method response"
    
    node = URLNode(segment="api", path="/api", parent=None)
    controller = Controller()
    
    # Store the bound method reference
    bound_method = controller.handle_get
    node.attach_handler("GET", bound_method)
    
    # Verify the handler is stored and callable
    stored_handler = node._handlers.get("GET")
    if stored_handler is None:
        errmsg = "Expected handler to be stored"
        raise AssertionError(errmsg)
    
    # Verify the handler can be called and returns expected value
    result = stored_handler()
    if result != "class method response":
        errmsg = f"Expected 'class method response', got '{result}'"
        raise AssertionError(errmsg)
    
    return


# =============================================================================
# Unit Tests for get_handler Method
# =============================================================================

def test_urlnode_get_handler_returns_attached_handler():
    """
        Test that get_handler returns the attached handler.
        
        Validates: Requirements 3.6
    """
    node = URLNode(segment="api", path="/api", parent=None)
    
    def handler():
        return "response"
    
    node.attach_handler("GET", handler)
    
    result = node.get_handler("GET")
    
    if result is not handler:
        errmsg = "Expected get_handler to return the attached handler"
        raise AssertionError(errmsg)
    
    return


def test_urlnode_get_handler_returns_none_for_missing_method():
    """
        Test that get_handler returns None for non-existent method.
        
        Validates: Requirements 3.6
    """
    node = URLNode(segment="api", path="/api", parent=None)
    
    result = node.get_handler("GET")
    
    if result is not None:
        errmsg = f"Expected None, got {result}"
        raise AssertionError(errmsg)
    
    return


def test_urlnode_get_handler_normalizes_method_to_uppercase():
    """
        Test that get_handler normalizes method name to uppercase.
        
        Validates: Requirements 3.6
    """
    node = URLNode(segment="api", path="/api", parent=None)
    
    def handler():
        pass
    
    node.attach_handler("GET", handler)
    
    # Should find handler with lowercase method name
    result = node.get_handler("get")
    
    if result is not handler:
        errmsg = "Expected get_handler('get') to return handler attached with 'GET'"
        raise AssertionError(errmsg)
    
    return


def test_urlnode_get_handler_multiple_methods():
    """
        Test that get_handler returns correct handler for each method.
        
        Validates: Requirements 3.7
    """
    node = URLNode(segment="api", path="/api", parent=None)
    
    def get_handler():
        return "get"
    
    def post_handler():
        return "post"
    
    node.attach_handler("GET", get_handler)
    node.attach_handler("POST", post_handler)
    
    if node.get_handler("GET") is not get_handler:
        errmsg = "Expected get_handler('GET') to return get_handler"
        raise AssertionError(errmsg)
    
    if node.get_handler("POST") is not post_handler:
        errmsg = "Expected get_handler('POST') to return post_handler"
        raise AssertionError(errmsg)
    
    return


def test_urlnode_get_handler_mixed_case_methods():
    """
        Test that get_handler works with various case combinations.
    """
    node = URLNode(segment="api", path="/api", parent=None)
    
    def handler():
        pass
    
    node.attach_handler("POST", handler)
    
    # All these should return the same handler
    if node.get_handler("POST") is not handler:
        errmsg = "Expected get_handler('POST') to return handler"
        raise AssertionError(errmsg)
    
    if node.get_handler("post") is not handler:
        errmsg = "Expected get_handler('post') to return handler"
        raise AssertionError(errmsg)
    
    if node.get_handler("Post") is not handler:
        errmsg = "Expected get_handler('Post') to return handler"
        raise AssertionError(errmsg)
    
    if node.get_handler("pOsT") is not handler:
        errmsg = "Expected get_handler('pOsT') to return handler"
        raise AssertionError(errmsg)
    
    return


def test_urlnode_get_handler_returns_none_for_different_method():
    """
        Test that get_handler returns None for a different method.
    """
    node = URLNode(segment="api", path="/api", parent=None)
    
    def handler():
        pass
    
    node.attach_handler("GET", handler)
    
    if node.get_handler("POST") is not None:
        errmsg = "Expected get_handler('POST') to return None"
        raise AssertionError(errmsg)
    
    if node.get_handler("PUT") is not None:
        errmsg = "Expected get_handler('PUT') to return None"
        raise AssertionError(errmsg)
    
    return


# =============================================================================
# Integration Tests for Handler Attachment
# =============================================================================

def test_urlnode_handler_attachment_with_child_nodes():
    """
        Test that handler attachment works correctly with child nodes.
        
        Validates: Requirements 3.6, 3.7
    """
    root = URLNode(segment="", path="/", parent=None)
    api = root.add_child("api")
    users = api.add_child("users")
    
    def root_handler():
        return "root"
    
    def api_handler():
        return "api"
    
    def users_get_handler():
        return "users get"
    
    def users_post_handler():
        return "users post"
    
    root.attach_handler("GET", root_handler)
    api.attach_handler("GET", api_handler)
    users.attach_handler("GET", users_get_handler)
    users.attach_handler("POST", users_post_handler)
    
    # Verify each node has correct handlers
    if root.get_handler("GET") is not root_handler:
        errmsg = "Expected root to have root_handler"
        raise AssertionError(errmsg)
    
    if api.get_handler("GET") is not api_handler:
        errmsg = "Expected api to have api_handler"
        raise AssertionError(errmsg)
    
    if users.get_handler("GET") is not users_get_handler:
        errmsg = "Expected users to have users_get_handler for GET"
        raise AssertionError(errmsg)
    
    if users.get_handler("POST") is not users_post_handler:
        errmsg = "Expected users to have users_post_handler for POST"
        raise AssertionError(errmsg)
    
    # Verify is_leaf status
    if root.is_leaf is not True:
        errmsg = "Expected root.is_leaf to be True"
        raise AssertionError(errmsg)
    
    if api.is_leaf is not True:
        errmsg = "Expected api.is_leaf to be True"
        raise AssertionError(errmsg)
    
    if users.is_leaf is not True:
        errmsg = "Expected users.is_leaf to be True"
        raise AssertionError(errmsg)
    
    return


def test_urlnode_intermediate_node_not_leaf():
    """
        Test that intermediate nodes without handlers are not leaves.
        
        Validates: Requirements 1.5, 3.6
    """
    root = URLNode(segment="", path="/", parent=None)
    api = root.add_child("api")
    v1 = api.add_child("v1")
    users = v1.add_child("users")
    
    def users_handler():
        return "users"
    
    # Only attach handler to the leaf node
    users.attach_handler("GET", users_handler)
    
    # Intermediate nodes should not be leaves
    if root.is_leaf is not False:
        errmsg = "Expected root.is_leaf to be False"
        raise AssertionError(errmsg)
    
    if api.is_leaf is not False:
        errmsg = "Expected api.is_leaf to be False"
        raise AssertionError(errmsg)
    
    if v1.is_leaf is not False:
        errmsg = "Expected v1.is_leaf to be False"
        raise AssertionError(errmsg)
    
    # Only users should be a leaf
    if users.is_leaf is not True:
        errmsg = "Expected users.is_leaf to be True"
        raise AssertionError(errmsg)
    
    return


def test_urlnode_handler_callable_execution():
    """
        Test that attached handlers can be called and return expected values.
    """
    node = URLNode(segment="api", path="/api", parent=None)
    
    def get_handler(request):
        return {"method": "GET", "data": request}
    
    def post_handler(request, body):
        return {"method": "POST", "data": request, "body": body}
    
    node.attach_handler("GET", get_handler)
    node.attach_handler("POST", post_handler)
    
    # Execute the handlers
    get_result = node.get_handler("GET")("test_request")
    post_result = node.get_handler("POST")("test_request", {"key": "value"})
    
    if get_result != {"method": "GET", "data": "test_request"}:
        errmsg = f"Unexpected GET result: {get_result}"
        raise AssertionError(errmsg)
    
    if post_result != {"method": "POST", "data": "test_request", "body": {"key": "value"}}:
        errmsg = f"Unexpected POST result: {post_result}"
        raise AssertionError(errmsg)
    
    return
