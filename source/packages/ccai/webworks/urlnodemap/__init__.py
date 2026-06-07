"""
    URL Node Map package for hierarchical URL path organization.
    
    This package provides the foundational hierarchical tree structure
    for organizing HTTP endpoints in the ccai web framework.
"""

from ccai.webworks.urlnodemap.pathutils import (
    normalize_path,
    split_path,
    is_parameter_segment,
    extract_parameter_name,
)

from ccai.webworks.urlnodemap.exceptions import (
    NodeNotFoundError,
    NodeConflictError,
    PathConflictError,
    FrozenTreeError,
    HandlerConflictError,
    NodeHasChildrenError,
)

from ccai.webworks.urlnodemap.urlnode import URLNode
from ccai.webworks.urlnodemap.urlnodemap import URLNodeMap

__all__ = [
    # Path utilities
    "normalize_path",
    "split_path",
    "is_parameter_segment",
    "extract_parameter_name",
    # Exceptions
    "NodeNotFoundError",
    "NodeConflictError",
    "PathConflictError",
    "FrozenTreeError",
    "HandlerConflictError",
    "NodeHasChildrenError",
    # Classes
    "URLNode",
    "URLNodeMap",
]
