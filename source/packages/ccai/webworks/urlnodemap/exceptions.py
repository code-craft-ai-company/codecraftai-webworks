"""
    Exception classes for the URL Node Map package.
    
    This module defines custom exceptions used throughout the URL Node Map
    feature for error handling and validation.
"""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from typing import Callable
    from ccai.webworks.urlnodemap.urlnode import URLNode


class NodeNotFoundError(Exception):
    """
        Raised when a node path does not exist in the tree.
        
        :param path: The path that was not found.
    """
    
    def __init__(self, path: str):
        self.path = path
        super().__init__(f"Node not found at path: {path}")


class NodeConflictError(Exception):
    """
        Raised when a node already exists at the specified path.
        
        :param path: The path where the conflict occurred.
        :param existing_node: The node that already exists at the path.
    """
    
    def __init__(self, path: str, existing_node: "URLNode"):
        self.path = path
        self.existing_node = existing_node
        super().__init__(f"Node already exists at path: {path}")


class PathConflictError(Exception):
    """
        Raised when parameter and literal segments conflict.
        
        :param path: The path where the conflict occurred.
        :param parameter_segment: The parameter segment involved in the conflict.
        :param literal_segment: The literal segment involved in the conflict.
    """
    
    def __init__(self, path: str, parameter_segment: str, literal_segment: str):
        self.path = path
        self.parameter_segment = parameter_segment
        self.literal_segment = literal_segment
        super().__init__(
            f"Parameter segment '{parameter_segment}' conflicts with "
            f"literal segment '{literal_segment}' at path: {path}"
        )


class FrozenTreeError(Exception):
    """
        Raised when attempting to modify a frozen URL node map.
    """
    
    def __init__(self):
        super().__init__("Cannot modify frozen URL node map")


class HandlerConflictError(Exception):
    """
        Raised when a handler already exists for the specified method.
        
        :param path: The path where the conflict occurred.
        :param method: The HTTP method that has a conflicting handler.
        :param existing_handler: The handler that already exists.
    """
    
    def __init__(self, path: str, method: str, existing_handler: "Callable"):
        self.path = path
        self.method = method
        self.existing_handler = existing_handler
        super().__init__(
            f"Handler already exists for {method} at path: {path}"
        )


class NodeHasChildrenError(Exception):
    """
        Raised when attempting to remove a node with children.
        
        :param path: The path of the node that has children.
        :param child_count: The number of children the node has.
    """
    
    def __init__(self, path: str, child_count: int):
        self.path = path
        self.child_count = child_count
        super().__init__(
            f"Cannot remove node at {path}: has {child_count} children. "
            "Use recursive=True to remove with children."
        )
