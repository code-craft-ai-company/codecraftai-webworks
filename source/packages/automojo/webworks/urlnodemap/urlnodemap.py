"""
    URLNodeMap class for the URL Node Map package.
    
    This module provides the URLNodeMap class which represents the hierarchical
    tree structure for organizing URL paths and endpoint metadata. The map
    supports path-based addressing, node creation, removal, and thread-safe
    operations.
"""

from __future__ import annotations

import threading
from typing import Iterator, TYPE_CHECKING

from automojo.webworks.urlnodemap.pathutils import normalize_path, split_path
from automojo.webworks.urlnodemap.urlnode import URLNode
from automojo.webworks.urlnodemap.exceptions import (
    NodeNotFoundError,
    FrozenTreeError,
    NodeHasChildrenError,
)

if TYPE_CHECKING:
    pass


class URLNodeMap:
    """
        Hierarchical tree structure for organizing URL paths and endpoint metadata.
        
        The URLNodeMap provides the foundational data structure for organizing
        HTTP endpoints in a tree hierarchy. Each path segment corresponds to a
        node in the tree, and nodes can carry metadata (access policies, rate
        limits, tags) that can be inherited by child nodes.
        
        The map supports:
        - Path-based node addressing (get_node, get_or_create_node, has_node)
        - Node removal with optional recursive deletion
        - Thread-safe modifications via RLock
        - Freezing for lock-free concurrent reads
        
        Example usage::
        
            node_map = URLNodeMap()
            
            # Create nodes for a path
            users_node = node_map.get_or_create_node("/api/v1/users")
            
            # Check if a path exists
            if node_map.has_node("/api/v1/users"):
                node = node_map.get_node("/api/v1/users")
            
            # Remove a node
            node_map.remove_node("/api/v1/users", recursive=True)
    """
    
    def __init__(self):
        """
            Initialize the URL node map with a root node.
            
            Creates a new URLNodeMap with an empty root node representing
            the base path "/". The map starts in an unfrozen state allowing
            modifications.
        """
        self._frozen: bool = False
        self._lock: threading.RLock = threading.RLock()
        self._root: URLNode = URLNode(
            segment="",
            path="/",
            parent=None,
            frozen_checker=self._check_frozen
        )

    @property
    def root(self) -> URLNode:
        """
            Return the root node of the tree.
            
            The root node represents the base path "/" and is the ancestor
            of all other nodes in the tree.
            
            :returns: The root URLNode.
        """
        return self._root
    
    @property
    def frozen(self) -> bool:
        """
            Return True if the tree is frozen.
            
            A frozen tree cannot be modified. All modification operations
            will raise FrozenTreeError.
            
            :returns: True if the tree is frozen, False otherwise.
        """
        return self._frozen
    
    def _check_frozen(self) -> None:
        """
            Check if the tree is frozen and raise if so.
            
            :raises FrozenTreeError: If the tree is frozen.
        """
        if self._frozen:
            raise FrozenTreeError()

    def freeze(self) -> None:
        """
            Make the tree immutable for lock-free concurrent reads.
            
            After freezing, any modification attempt (add_child, remove_node,
            set_metadata, attach_handler) raises FrozenTreeError. This allows
            safe concurrent read access without locking.
        """
        self._frozen = True
    
    def get_node(self, path: str) -> URLNode:
        """
            Retrieve a node by its full path.
            
            Traverses the tree from the root following each path segment
            to locate the target node. The path is normalized before lookup.
            
            :param path: The full path to the node (e.g., "/api/v1/users").
            
            :returns: The URLNode at the specified path.
            
            :raises NodeNotFoundError: If the path does not exist in the tree.
        """
        normalized = normalize_path(path)
        
        # Root path is a special case
        if normalized == "/":
            return self._root
        
        # Split the path into segments and traverse
        segments = split_path(normalized)
        current = self._root
        
        for segment in segments:
            if segment not in current._children:
                raise NodeNotFoundError(normalized)
            current = current._children[segment]
        
        return current
    
    def get_or_create_node(self, path: str) -> URLNode:
        """
            Retrieve an existing node or create the path if it does not exist.
            
            Traverses the tree from the root, creating any intermediate nodes
            necessary to reach the target path. This ensures all ancestor nodes
            exist before the target node is created.
            
            :param path: The full path to the node.
            
            :returns: The URLNode at the specified path (created if necessary).
            
            :raises FrozenTreeError: If the tree is frozen and creation is needed.
        """
        normalized = normalize_path(path)
        
        # Root path is a special case
        if normalized == "/":
            return self._root
        
        # Split the path into segments
        segments = split_path(normalized)
        
        with self._lock:
            current = self._root
            
            for segment in segments:
                if segment in current._children:
                    # Node exists, continue traversal
                    current = current._children[segment]
                else:
                    # Node doesn't exist, need to create it
                    self._check_frozen()
                    current = current.add_child(segment)
            
            return current
    
    def has_node(self, path: str) -> bool:
        """
            Check if a path exists in the tree.
            
            :param path: The full path to check.
            
            :returns: True if the path exists, False otherwise.
        """
        normalized = normalize_path(path)
        
        # Root path always exists
        if normalized == "/":
            return True
        
        # Split the path into segments and traverse
        segments = split_path(normalized)
        current = self._root
        
        for segment in segments:
            if segment not in current._children:
                return False
            current = current._children[segment]
        
        return True
    
    def remove_node(self, path: str, recursive: bool = False) -> None:
        """
            Remove a node from the tree.
            
            Removes the node at the specified path. If the node has children
            and recursive is False, raises NodeHasChildrenError. If recursive
            is True, removes the node and all its descendants.
            
            The root node cannot be removed.
            
            :param path: The full path of the node to remove.
            :param recursive: If True, remove all descendants as well.
            
            :raises NodeNotFoundError: If the path does not exist.
            :raises FrozenTreeError: If the tree is frozen.
            :raises NodeHasChildrenError: If recursive=False and node has children.
            :raises ValueError: If attempting to remove the root node.
        """
        normalized = normalize_path(path)
        
        # Cannot remove root node
        if normalized == "/":
            raise ValueError("Cannot remove root node")
        
        with self._lock:
            self._check_frozen()
            
            # Find the node and its parent
            segments = split_path(normalized)
            
            # Traverse to the parent of the target node
            parent = self._root
            for segment in segments[:-1]:
                if segment not in parent._children:
                    raise NodeNotFoundError(normalized)
                parent = parent._children[segment]
            
            # Get the target segment
            target_segment = segments[-1]
            
            # Check if target exists
            if target_segment not in parent._children:
                raise NodeNotFoundError(normalized)
            
            target_node = parent._children[target_segment]
            
            # Check for children if not recursive
            if not recursive and len(target_node._children) > 0:
                raise NodeHasChildrenError(normalized, len(target_node._children))
            
            # Remove the node from parent's children
            del parent._children[target_segment]

    def iterate_nodes(self) -> Iterator[URLNode]:
        """
            Iterate over all nodes in depth-first order.

            Performs a depth-first traversal of the entire tree, starting
            with the root node and visiting all descendants. Every node in
            the tree is yielded exactly once.

            :yields: URLNode instances in depth-first traversal order.
        """
        yield self._root
        yield from self._root.descendants()

    def iterate_leaves(self) -> Iterator[URLNode]:
        """
            Iterate over all leaf nodes (nodes with handlers).

            Traverses the entire tree in depth-first order and yields only
            those nodes that have at least one HTTP method handler attached
            (i.e., nodes where ``is_leaf`` is True).

            :yields: URLNode instances that have handlers attached.
        """
        for node in self.iterate_nodes():
            if node.is_leaf:
                yield node

    def export_tree(self) -> dict:
        """
            Serialize the tree structure to a dictionary.

            Recursively converts the URL tree into a nested dictionary
            representation. Each node is represented as a dictionary with
            its segment, path, metadata, handlers, and children.

            :returns: Dictionary representation of the tree.
        """

        def _serialize_node(node: URLNode) -> dict:
            """
                Serialize a single node and its descendants to a dictionary.

                :param node: The URLNode to serialize.

                :returns: Dictionary representation of the node.
            """
            result = {
                "segment": node.segment,
                "path": node.path,
                "is_parameter": node.is_parameter,
                "metadata": node.metadata,
                "handlers": sorted(
                    method for method in node._handlers
                ),
                "children": {
                    seg: _serialize_node(child)
                    for seg, child in node.children.items()
                },
            }
            return result

        return _serialize_node(self._root)

    def export_routes(self) -> list:
        """
            Export a flat list of all routes with their metadata.

            Iterates over all leaf nodes in the tree and collects their
            resolved metadata using the inheritance chain. Each entry
            represents a single endpoint with its effective configuration.

            :returns: List of route dictionaries with resolved metadata.
        """
        routes = []

        for leaf in self.iterate_leaves():
            methods = sorted(leaf._handlers.keys())
            handler_names = []
            for method in methods:
                handler = leaf._handlers[method]
                handler_name = getattr(handler, "__name__", str(handler))
                handler_names.append(handler_name)

            handler_str = ", ".join(handler_names) if handler_names else None

            access_policy = leaf.get_effective_access_policy()
            if access_policy is not None:
                access_policy = str(access_policy)

            rate_limit = leaf.get_effective_rate_limit()
            if rate_limit is not None:
                rate_limit = str(rate_limit)

            tags = leaf.get_effective_tags()
            version = leaf.get_effective_metadata("version")
            scopes = leaf.get_effective_metadata("scopes") or []
            extras = leaf.get_effective_metadata("extras") or {}

            route = {
                "path": leaf.path,
                "methods": methods,
                "handler": handler_str,
                "access_policy": access_policy,
                "rate_limit": rate_limit,
                "tags": tags,
                "version": version,
                "scopes": scopes,
                "extras": extras,
            }
            routes.append(route)

        return routes

    def export_security_map(self, filter_tag: str = None) -> list:
        """
            Export security-focused route information for auditing.

            Iterates over all leaf nodes and collects security-relevant
            metadata. Optionally filters routes by a specific tag.

            :param filter_tag: Optional tag to filter routes. When provided,
                only routes whose effective tags include this tag are included.

            :returns: List of security map entry dictionaries.
        """
        entries = []

        for leaf in self.iterate_leaves():
            tags = leaf.get_effective_tags()

            if filter_tag is not None and filter_tag not in tags:
                continue

            methods = sorted(leaf._handlers.keys())
            handler_names = []
            for method in methods:
                handler = leaf._handlers[method]
                handler_name = getattr(handler, "__name__", str(handler))
                handler_names.append(handler_name)

            handler_str = ", ".join(handler_names) if handler_names else ""

            access_policy = leaf.get_effective_access_policy()
            access_policy_str = str(access_policy) if access_policy is not None else ""

            scopes = leaf.get_effective_metadata("scopes") or []

            rate_limit = leaf.get_effective_rate_limit()
            rate_limit_str = str(rate_limit) if rate_limit is not None else ""

            methods_str = ", ".join(methods)
            summary = f"{methods_str} {leaf.path}"
            if access_policy_str:
                summary += f" [{access_policy_str}]"

            entry = {
                "path": leaf.path,
                "methods": methods,
                "handler": handler_str,
                "access_policy": access_policy_str,
                "scopes": scopes,
                "rate_limit": rate_limit_str,
                "summary": summary,
            }
            entries.append(entry)

        return entries


