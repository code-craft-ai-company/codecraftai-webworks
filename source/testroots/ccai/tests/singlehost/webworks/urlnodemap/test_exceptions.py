"""
    Tests for the URL Node Map exception classes.
    
    This module contains unit tests for the exception classes
    (NodeNotFoundError, NodeConflictError, PathConflictError, FrozenTreeError,
    HandlerConflictError, NodeHasChildrenError) used throughout the URL Node Map
    implementation.
    
    Validates: Requirements 1.8, 2.5, 7.7, 8.4
"""

from ccai.webworks.urlnodemap.exceptions import (
    NodeNotFoundError,
    NodeConflictError,
    PathConflictError,
    FrozenTreeError,
    HandlerConflictError,
    NodeHasChildrenError,
)


# =============================================================================
# Unit Tests for NodeNotFoundError
# =============================================================================

def test_node_not_found_error_stores_path():
    """
        Test that NodeNotFoundError stores the path attribute.
        
        Validates: Requirements 2.5
    """
    path = "/api/v1/users"
    error = NodeNotFoundError(path)
    
    if error.path != path:
        errmsg = f"Expected path '{path}', got '{error.path}'"
        raise AssertionError(errmsg)
    
    return


def test_node_not_found_error_message_contains_path():
    """
        Test that NodeNotFoundError message contains the path.
        
        Validates: Requirements 2.5
    """
    path = "/api/v1/users"
    error = NodeNotFoundError(path)
    
    message = str(error)
    if path not in message:
        errmsg = f"Expected path '{path}' in message, got '{message}'"
        raise AssertionError(errmsg)
    
    return


def test_node_not_found_error_is_exception():
    """
        Test that NodeNotFoundError is an Exception subclass.
    """
    error = NodeNotFoundError("/test")
    
    if not isinstance(error, Exception):
        errmsg = "NodeNotFoundError should be an Exception subclass"
        raise AssertionError(errmsg)
    
    return


def test_node_not_found_error_can_be_raised():
    """
        Test that NodeNotFoundError can be raised and caught.
    """
    path = "/api/v1/missing"
    caught = False
    
    try:
        raise NodeNotFoundError(path)
    except NodeNotFoundError as e:
        caught = True
        if e.path != path:
            errmsg = f"Expected path '{path}', got '{e.path}'"
            raise AssertionError(errmsg)
    
    if not caught:
        errmsg = "NodeNotFoundError was not caught"
        raise AssertionError(errmsg)
    
    return


# =============================================================================
# Unit Tests for NodeConflictError
# =============================================================================

def test_node_conflict_error_stores_path():
    """
        Test that NodeConflictError stores the path attribute.
        
        Validates: Requirements 1.8
    """
    path = "/api/v1/users"
    # Use a simple object as mock existing node
    existing_node = object()
    error = NodeConflictError(path, existing_node)
    
    if error.path != path:
        errmsg = f"Expected path '{path}', got '{error.path}'"
        raise AssertionError(errmsg)
    
    return


def test_node_conflict_error_stores_existing_node():
    """
        Test that NodeConflictError stores the existing_node attribute.
        
        Validates: Requirements 1.8
    """
    path = "/api/v1/users"
    existing_node = object()
    error = NodeConflictError(path, existing_node)
    
    if error.existing_node is not existing_node:
        errmsg = "Expected existing_node to be stored"
        raise AssertionError(errmsg)
    
    return


def test_node_conflict_error_message_contains_path():
    """
        Test that NodeConflictError message contains the path.
        
        Validates: Requirements 1.8
    """
    path = "/api/v1/users"
    existing_node = object()
    error = NodeConflictError(path, existing_node)
    
    message = str(error)
    if path not in message:
        errmsg = f"Expected path '{path}' in message, got '{message}'"
        raise AssertionError(errmsg)
    
    return


def test_node_conflict_error_is_exception():
    """
        Test that NodeConflictError is an Exception subclass.
    """
    error = NodeConflictError("/test", object())
    
    if not isinstance(error, Exception):
        errmsg = "NodeConflictError should be an Exception subclass"
        raise AssertionError(errmsg)
    
    return


def test_node_conflict_error_can_be_raised():
    """
        Test that NodeConflictError can be raised and caught.
    """
    path = "/api/v1/existing"
    existing_node = object()
    caught = False
    
    try:
        raise NodeConflictError(path, existing_node)
    except NodeConflictError as e:
        caught = True
        if e.path != path:
            errmsg = f"Expected path '{path}', got '{e.path}'"
            raise AssertionError(errmsg)
        if e.existing_node is not existing_node:
            errmsg = "Expected existing_node to be preserved"
            raise AssertionError(errmsg)
    
    if not caught:
        errmsg = "NodeConflictError was not caught"
        raise AssertionError(errmsg)
    
    return


# =============================================================================
# Unit Tests for PathConflictError
# =============================================================================

def test_path_conflict_error_stores_path():
    """
        Test that PathConflictError stores the path attribute.
        
        Validates: Requirements 7.7
    """
    path = "/api/v1"
    parameter_segment = "{id}"
    literal_segment = "users"
    error = PathConflictError(path, parameter_segment, literal_segment)
    
    if error.path != path:
        errmsg = f"Expected path '{path}', got '{error.path}'"
        raise AssertionError(errmsg)
    
    return


def test_path_conflict_error_stores_parameter_segment():
    """
        Test that PathConflictError stores the parameter_segment attribute.
        
        Validates: Requirements 7.7
    """
    path = "/api/v1"
    parameter_segment = "{id}"
    literal_segment = "users"
    error = PathConflictError(path, parameter_segment, literal_segment)
    
    if error.parameter_segment != parameter_segment:
        errmsg = f"Expected parameter_segment '{parameter_segment}', got '{error.parameter_segment}'"
        raise AssertionError(errmsg)
    
    return


def test_path_conflict_error_stores_literal_segment():
    """
        Test that PathConflictError stores the literal_segment attribute.
        
        Validates: Requirements 7.7
    """
    path = "/api/v1"
    parameter_segment = "{id}"
    literal_segment = "users"
    error = PathConflictError(path, parameter_segment, literal_segment)
    
    if error.literal_segment != literal_segment:
        errmsg = f"Expected literal_segment '{literal_segment}', got '{error.literal_segment}'"
        raise AssertionError(errmsg)
    
    return


def test_path_conflict_error_message_contains_all_info():
    """
        Test that PathConflictError message contains all relevant information.
        
        Validates: Requirements 7.7
    """
    path = "/api/v1"
    parameter_segment = "{id}"
    literal_segment = "users"
    error = PathConflictError(path, parameter_segment, literal_segment)
    
    message = str(error)
    if parameter_segment not in message:
        errmsg = f"Expected parameter_segment '{parameter_segment}' in message, got '{message}'"
        raise AssertionError(errmsg)
    
    if literal_segment not in message:
        errmsg = f"Expected literal_segment '{literal_segment}' in message, got '{message}'"
        raise AssertionError(errmsg)
    
    if path not in message:
        errmsg = f"Expected path '{path}' in message, got '{message}'"
        raise AssertionError(errmsg)
    
    return


def test_path_conflict_error_is_exception():
    """
        Test that PathConflictError is an Exception subclass.
    """
    error = PathConflictError("/test", "{id}", "users")
    
    if not isinstance(error, Exception):
        errmsg = "PathConflictError should be an Exception subclass"
        raise AssertionError(errmsg)
    
    return


def test_path_conflict_error_can_be_raised():
    """
        Test that PathConflictError can be raised and caught.
    """
    path = "/api/v1"
    parameter_segment = "{id}"
    literal_segment = "users"
    caught = False
    
    try:
        raise PathConflictError(path, parameter_segment, literal_segment)
    except PathConflictError as e:
        caught = True
        if e.path != path:
            errmsg = f"Expected path '{path}', got '{e.path}'"
            raise AssertionError(errmsg)
        if e.parameter_segment != parameter_segment:
            errmsg = f"Expected parameter_segment '{parameter_segment}', got '{e.parameter_segment}'"
            raise AssertionError(errmsg)
        if e.literal_segment != literal_segment:
            errmsg = f"Expected literal_segment '{literal_segment}', got '{e.literal_segment}'"
            raise AssertionError(errmsg)
    
    if not caught:
        errmsg = "PathConflictError was not caught"
        raise AssertionError(errmsg)
    
    return


# =============================================================================
# Unit Tests for FrozenTreeError
# =============================================================================

def test_frozen_tree_error_has_message():
    """
        Test that FrozenTreeError has a descriptive message.
        
        Validates: Requirements 8.4
    """
    error = FrozenTreeError()
    
    message = str(error)
    if not message:
        errmsg = "FrozenTreeError should have a message"
        raise AssertionError(errmsg)
    
    # Message should mention frozen or modify
    message_lower = message.lower()
    if "frozen" not in message_lower and "modify" not in message_lower:
        errmsg = f"Expected message to mention 'frozen' or 'modify', got '{message}'"
        raise AssertionError(errmsg)
    
    return


def test_frozen_tree_error_is_exception():
    """
        Test that FrozenTreeError is an Exception subclass.
    """
    error = FrozenTreeError()
    
    if not isinstance(error, Exception):
        errmsg = "FrozenTreeError should be an Exception subclass"
        raise AssertionError(errmsg)
    
    return


def test_frozen_tree_error_can_be_raised():
    """
        Test that FrozenTreeError can be raised and caught.
        
        Validates: Requirements 8.4
    """
    caught = False
    
    try:
        raise FrozenTreeError()
    except FrozenTreeError:
        caught = True
    
    if not caught:
        errmsg = "FrozenTreeError was not caught"
        raise AssertionError(errmsg)
    
    return


def test_frozen_tree_error_no_arguments_required():
    """
        Test that FrozenTreeError requires no arguments.
        
        Validates: Requirements 8.4
    """
    # Should not raise any exception
    error = FrozenTreeError()
    
    if error is None:
        errmsg = "FrozenTreeError should be instantiable without arguments"
        raise AssertionError(errmsg)
    
    return


# =============================================================================
# Unit Tests for HandlerConflictError
# =============================================================================

def test_handler_conflict_error_stores_path():
    """
        Test that HandlerConflictError stores the path attribute.
    """
    path = "/api/v1/users"
    method = "GET"
    existing_handler = lambda: None
    error = HandlerConflictError(path, method, existing_handler)
    
    if error.path != path:
        errmsg = f"Expected path '{path}', got '{error.path}'"
        raise AssertionError(errmsg)
    
    return


def test_handler_conflict_error_stores_method():
    """
        Test that HandlerConflictError stores the method attribute.
    """
    path = "/api/v1/users"
    method = "GET"
    existing_handler = lambda: None
    error = HandlerConflictError(path, method, existing_handler)
    
    if error.method != method:
        errmsg = f"Expected method '{method}', got '{error.method}'"
        raise AssertionError(errmsg)
    
    return


def test_handler_conflict_error_stores_existing_handler():
    """
        Test that HandlerConflictError stores the existing_handler attribute.
    """
    path = "/api/v1/users"
    method = "GET"
    existing_handler = lambda: None
    error = HandlerConflictError(path, method, existing_handler)
    
    if error.existing_handler is not existing_handler:
        errmsg = "Expected existing_handler to be stored"
        raise AssertionError(errmsg)
    
    return


def test_handler_conflict_error_message_contains_method_and_path():
    """
        Test that HandlerConflictError message contains method and path.
    """
    path = "/api/v1/users"
    method = "POST"
    existing_handler = lambda: None
    error = HandlerConflictError(path, method, existing_handler)
    
    message = str(error)
    if method not in message:
        errmsg = f"Expected method '{method}' in message, got '{message}'"
        raise AssertionError(errmsg)
    
    if path not in message:
        errmsg = f"Expected path '{path}' in message, got '{message}'"
        raise AssertionError(errmsg)
    
    return


def test_handler_conflict_error_is_exception():
    """
        Test that HandlerConflictError is an Exception subclass.
    """
    error = HandlerConflictError("/test", "GET", lambda: None)
    
    if not isinstance(error, Exception):
        errmsg = "HandlerConflictError should be an Exception subclass"
        raise AssertionError(errmsg)
    
    return


def test_handler_conflict_error_can_be_raised():
    """
        Test that HandlerConflictError can be raised and caught.
    """
    path = "/api/v1/users"
    method = "DELETE"
    existing_handler = lambda: None
    caught = False
    
    try:
        raise HandlerConflictError(path, method, existing_handler)
    except HandlerConflictError as e:
        caught = True
        if e.path != path:
            errmsg = f"Expected path '{path}', got '{e.path}'"
            raise AssertionError(errmsg)
        if e.method != method:
            errmsg = f"Expected method '{method}', got '{e.method}'"
            raise AssertionError(errmsg)
        if e.existing_handler is not existing_handler:
            errmsg = "Expected existing_handler to be preserved"
            raise AssertionError(errmsg)
    
    if not caught:
        errmsg = "HandlerConflictError was not caught"
        raise AssertionError(errmsg)
    
    return


# =============================================================================
# Unit Tests for NodeHasChildrenError
# =============================================================================

def test_node_has_children_error_stores_path():
    """
        Test that NodeHasChildrenError stores the path attribute.
    """
    path = "/api/v1"
    child_count = 3
    error = NodeHasChildrenError(path, child_count)
    
    if error.path != path:
        errmsg = f"Expected path '{path}', got '{error.path}'"
        raise AssertionError(errmsg)
    
    return


def test_node_has_children_error_stores_child_count():
    """
        Test that NodeHasChildrenError stores the child_count attribute.
    """
    path = "/api/v1"
    child_count = 5
    error = NodeHasChildrenError(path, child_count)
    
    if error.child_count != child_count:
        errmsg = f"Expected child_count {child_count}, got {error.child_count}"
        raise AssertionError(errmsg)
    
    return


def test_node_has_children_error_message_contains_path_and_count():
    """
        Test that NodeHasChildrenError message contains path and child count.
    """
    path = "/api/v1"
    child_count = 7
    error = NodeHasChildrenError(path, child_count)
    
    message = str(error)
    if path not in message:
        errmsg = f"Expected path '{path}' in message, got '{message}'"
        raise AssertionError(errmsg)
    
    if str(child_count) not in message:
        errmsg = f"Expected child_count '{child_count}' in message, got '{message}'"
        raise AssertionError(errmsg)
    
    return


def test_node_has_children_error_message_mentions_recursive():
    """
        Test that NodeHasChildrenError message mentions recursive option.
    """
    path = "/api/v1"
    child_count = 2
    error = NodeHasChildrenError(path, child_count)
    
    message = str(error)
    if "recursive" not in message.lower():
        errmsg = f"Expected 'recursive' in message, got '{message}'"
        raise AssertionError(errmsg)
    
    return


def test_node_has_children_error_is_exception():
    """
        Test that NodeHasChildrenError is an Exception subclass.
    """
    error = NodeHasChildrenError("/test", 1)
    
    if not isinstance(error, Exception):
        errmsg = "NodeHasChildrenError should be an Exception subclass"
        raise AssertionError(errmsg)
    
    return


def test_node_has_children_error_can_be_raised():
    """
        Test that NodeHasChildrenError can be raised and caught.
    """
    path = "/api/v1/users"
    child_count = 4
    caught = False
    
    try:
        raise NodeHasChildrenError(path, child_count)
    except NodeHasChildrenError as e:
        caught = True
        if e.path != path:
            errmsg = f"Expected path '{path}', got '{e.path}'"
            raise AssertionError(errmsg)
        if e.child_count != child_count:
            errmsg = f"Expected child_count {child_count}, got {e.child_count}"
            raise AssertionError(errmsg)
    
    if not caught:
        errmsg = "NodeHasChildrenError was not caught"
        raise AssertionError(errmsg)
    
    return


# =============================================================================
# Integration Tests - Exception Hierarchy
# =============================================================================

def test_all_exceptions_are_exception_subclasses():
    """
        Test that all custom exceptions inherit from Exception.
    """
    exceptions = [
        NodeNotFoundError("/test"),
        NodeConflictError("/test", object()),
        PathConflictError("/test", "{id}", "users"),
        FrozenTreeError(),
        HandlerConflictError("/test", "GET", lambda: None),
        NodeHasChildrenError("/test", 1),
    ]
    
    for exc in exceptions:
        if not isinstance(exc, Exception):
            errmsg = f"{type(exc).__name__} should be an Exception subclass"
            raise AssertionError(errmsg)
    
    return


def test_exceptions_can_be_caught_as_exception():
    """
        Test that all custom exceptions can be caught as generic Exception.
    """
    exceptions_to_raise = [
        lambda: NodeNotFoundError("/test"),
        lambda: NodeConflictError("/test", object()),
        lambda: PathConflictError("/test", "{id}", "users"),
        lambda: FrozenTreeError(),
        lambda: HandlerConflictError("/test", "GET", lambda: None),
        lambda: NodeHasChildrenError("/test", 1),
    ]
    
    for exc_factory in exceptions_to_raise:
        caught = False
        try:
            raise exc_factory()
        except Exception:
            caught = True
        
        if not caught:
            errmsg = f"Exception from {exc_factory} was not caught as Exception"
            raise AssertionError(errmsg)
    
    return
