"""
    URLNode class for the URL Node Map package.
    
    This module provides the URLNode class which represents a single node
    in the URL tree. Each node corresponds to a path segment and can carry
    metadata, handlers, and references to parent and child nodes.
"""

from __future__ import annotations

from types import MappingProxyType
from typing import Any, Callable, Dict, Iterator, List, Mapping, Optional

from ccai.webworks.urlnodemap.pathutils import is_parameter_segment
from ccai.webworks.urlnodemap.exceptions import (
    NodeNotFoundError,
    NodeConflictError,
    PathConflictError,
    FrozenTreeError,
    HandlerConflictError,
)


class URLNode:
    """
        A single node in the URL tree representing a path segment.
        
        Each URLNode stores:
        - The path segment it represents
        - The full path from root to this node
        - A reference to its parent node (None for root)
        - A collection of child nodes
        - Metadata properties for access policies, rate limits, tags, etc.
        - HTTP method handlers for endpoint functionality
        
        Parameter segments (e.g., {user_id}) are automatically detected
        and the parameter name is extracted for routing purposes.
    """
    
    def __init__(
        self,
        segment: str,
        path: str,
        parent: Optional[URLNode] = None,
        frozen_checker: Optional[Callable[[], None]] = None
    ):
        """
            Initialize a URLNode.
            
            :param segment: The path segment this node represents.
            :param path: The full path from root to this node.
            :param parent: Reference to the parent node (None for root).
            :param frozen_checker: Optional callable that raises FrozenTreeError
                if the owning tree is frozen. Used to enforce immutability on
                node-level modification operations.
        """
        self._segment: str = segment
        self._path: str = path
        self._parent: Optional[URLNode] = parent
        self._children: Dict[str, URLNode] = {}
        self._metadata: Dict[str, Any] = {}
        self._handlers: Dict[str, Callable] = {}  # method -> handler
        self._is_parameter: bool = is_parameter_segment(segment)
        self._parameter_name: Optional[str] = None
        self._frozen_checker: Optional[Callable[[], None]] = frozen_checker
        if self._is_parameter:
            self._parameter_name = segment[1:-1]
    
    @property
    def segment(self) -> str:
        """
            Return the path segment for this node.
            
            :returns: The segment string (e.g., "api", "v1", "{user_id}").
        """
        return self._segment
    
    @property
    def path(self) -> str:
        """
            Return the full path from root to this node.
            
            :returns: The full path string (e.g., "/api/v1/users").
        """
        return self._path
    
    @property
    def parent(self) -> Optional[URLNode]:
        """
            Return the parent node or None for root.
            
            :returns: The parent URLNode or None if this is the root node.
        """
        return self._parent
    
    @property
    def children(self) -> Mapping[str, URLNode]:
        """
            Return an immutable view of child nodes.
            
            The returned mapping is read-only to prevent external modification
            of the tree structure. Use add_child() to add new children.
            
            :returns: An immutable mapping of segment names to child URLNodes.
        """
        return MappingProxyType(self._children)
    
    @property
    def is_parameter(self) -> bool:
        """
            Return True if this is a parameter segment.
            
            A parameter segment matches the pattern {param_name} and is used
            for dynamic routing where the segment value is captured as a
            route parameter.
            
            :returns: True if this node represents a parameter segment.
        """
        return self._is_parameter
    
    @property
    def parameter_name(self) -> Optional[str]:
        """
            Return the parameter name if this is a parameter segment.
            
            For a segment like "{user_id}", this returns "user_id".
            For non-parameter segments, this returns None.
            
            :returns: The parameter name or None if not a parameter segment.
        """
        return self._parameter_name

    @property
    def is_leaf(self) -> bool:
        """
            Return True if this node has handlers attached.
            
            A leaf node is one that has at least one HTTP method handler
            attached, making it an endpoint in the URL tree.
            
            :returns: True if this node has handlers attached.
        """
        return len(self._handlers) > 0

    @property
    def metadata(self) -> Dict[str, Any]:
        """
            Return a copy of the node's metadata.

            Returns a shallow copy of the metadata dictionary to prevent
            external modification of the internal state. Modifications to
            the returned dictionary will not affect the node's metadata.

            :returns: A dictionary copy of the node's metadata.
        """
        return dict(self._metadata)

    def get_metadata(self, key: str) -> Any:
        """
            Get a metadata value by key.

            Retrieves a metadata value from the node's metadata dictionary.
            Returns None if the key is not set.

            :param key: The metadata key.

            :returns: The metadata value or None if not set.
        """
        return self._metadata.get(key)

    def _check_frozen(self) -> None:
        """
            Check if the owning tree is frozen and raise if so.
            
            Delegates to the frozen_checker callback provided by the
            URLNodeMap that owns this node.
            
            :raises FrozenTreeError: If the owning tree is frozen.
        """
        if self._frozen_checker is not None:
            self._frozen_checker()

    def set_metadata(self, key: str, value: Any) -> None:
        """
            Set a metadata value.

            Sets or updates a metadata value in the node's metadata dictionary.

            :param key: The metadata key.
            :param value: The metadata value.

            :raises FrozenTreeError: If the owning tree is frozen.
        """
        self._check_frozen()
        self._metadata[key] = value

    def attach_handler(self, method: str, handler: Callable) -> None:
        """
            Attach a handler for a specific HTTP method.
            
            Associates a handler callable with an HTTP method for this node.
            The method name is normalized to uppercase (e.g., "get" becomes "GET").
            
            :param method: The HTTP method (GET, POST, PUT, DELETE, etc.).
            :param handler: The handler callable to attach.
            
            :raises HandlerConflictError: If a handler already exists for this method.
            :raises FrozenTreeError: If the owning tree is frozen.
        """
        self._check_frozen()
        method_upper = method.upper()
        
        if method_upper in self._handlers:
            raise HandlerConflictError(
                path=self._path,
                method=method_upper,
                existing_handler=self._handlers[method_upper]
            )
        
        self._handlers[method_upper] = handler

    def get_handler(self, method: str) -> Optional[Callable]:
        """
            Get the handler for a specific HTTP method.
            
            Retrieves the handler callable associated with the specified HTTP
            method. The method name is normalized to uppercase for lookup.
            
            :param method: The HTTP method (GET, POST, PUT, DELETE, etc.).
            
            :returns: The handler callable or None if not set.
        """
        return self._handlers.get(method.upper())

    
    def get_child(self, segment: str) -> URLNode:
        """
            Retrieve a direct child by segment name.
            
            :param segment: The segment name of the child.
            
            :returns: The child URLNode.
            
            :raises NodeNotFoundError: If no child with that segment exists.
        """
        if segment not in self._children:
            # Construct the expected child path for the error message
            if self._path == "/":
                child_path = f"/{segment}"
            else:
                child_path = f"{self._path}/{segment}"
            raise NodeNotFoundError(child_path)
        
        return self._children[segment]
    
    def add_child(self, segment: str, **metadata) -> URLNode:
        """
            Add a new child node.
            
            Creates a new URLNode as a child of this node with the given
            segment name. The child's full path is computed from this node's
            path plus the segment.
            
            :param segment: The segment name for the new child.
            :param metadata: Initial metadata for the child node.
            
            :returns: The newly created child URLNode.
            
            :raises NodeConflictError: If a child with that segment already exists.
            :raises PathConflictError: If parameter conflicts with literal segment.
            :raises FrozenTreeError: If the owning tree is frozen.
        """
        self._check_frozen()

        # Check if child already exists
        if segment in self._children:
            existing_child = self._children[segment]
            raise NodeConflictError(existing_child.path, existing_child)
        
        # Check for parameter/literal conflict
        new_is_parameter = is_parameter_segment(segment)
        
        for existing_segment, existing_child in self._children.items():
            existing_is_parameter = existing_child.is_parameter
            
            # Conflict: trying to add parameter when literal exists, or vice versa
            if new_is_parameter and not existing_is_parameter:
                # Adding parameter when literal exists
                if self._path == "/":
                    conflict_path = f"/{segment}"
                else:
                    conflict_path = f"{self._path}/{segment}"
                raise PathConflictError(conflict_path, segment, existing_segment)
            
            if not new_is_parameter and existing_is_parameter:
                # Adding literal when parameter exists
                if self._path == "/":
                    conflict_path = f"/{segment}"
                else:
                    conflict_path = f"{self._path}/{segment}"
                raise PathConflictError(conflict_path, existing_segment, segment)
        
        # Compute the child's full path
        if self._path == "/":
            child_path = f"/{segment}"
        else:
            child_path = f"{self._path}/{segment}"
        
        # Create the new child node
        child = URLNode(
            segment=segment,
            path=child_path,
            parent=self,
            frozen_checker=self._frozen_checker
        )
        
        # Apply initial metadata
        for key, value in metadata.items():
            child._metadata[key] = value
        
        # Add to children collection
        self._children[segment] = child
        
        return child

    def get_effective_metadata(self, key: str) -> Any:
        """
            Get metadata value with inheritance resolution.

            Walks up the tree from this node to the root, returning the first
            non-None value found for the given key. If no ancestor defines the
            key, returns None.

            :param key: The metadata key to resolve.

            :returns: The effective value considering inheritance from ancestors,
                or None if no node in the chain defines it.
        """
        current = self
        while current is not None:
            value = current._metadata.get(key)
            if value is not None:
                return value
            current = current._parent
        return None

    def get_effective_access_policy(self) -> Any:
        """
            Compute the combined access policy from the inheritance chain.

            Collects all access_policy values from this node up to the root
            and combines them via logical AND. If only one policy exists in
            the chain, it is returned directly. If no policy is set anywhere
            in the chain, returns None.

            Access policies are represented as strings or dicts. When multiple
            policies exist, they are collected into a list representing the
            AND-combined constraints.

            :returns: The combined access policy, a single policy if only one
                exists, or None if no policy is set.
        """
        policies = []
        current = self
        while current is not None:
            policy = current._metadata.get("access_policy")
            if policy is not None:
                policies.append(policy)
            current = current._parent

        if len(policies) == 0:
            return None
        if len(policies) == 1:
            return policies[0]
        return policies

    def get_effective_tags(self) -> List[str]:
        """
            Get merged tags from the inheritance chain.

            If this node has replace_tags=True in its metadata, only the
            node's own tags are returned. Otherwise, collects tags from all
            ancestors and merges them with this node's tags using set union,
            preserving a sorted order for deterministic results.

            :returns: A sorted list of unique tags merged from the inheritance
                chain, or only this node's tags if replace_tags is True.
        """
        if self._metadata.get("replace_tags", False):
            own_tags = self._metadata.get("tags", [])
            return sorted(set(own_tags))

        all_tags = set()
        current = self
        while current is not None:
            node_tags = current._metadata.get("tags", [])
            all_tags.update(node_tags)
            current = current._parent

        return sorted(all_tags)

    def get_effective_rate_limit(self) -> Any:
        """
            Get the most restrictive rate limit from the inheritance chain.

            Walks up the tree collecting rate limit values. The effective rate
            limit is the most restrictive (lowest numeric value) found in the
            chain. If a child node explicitly sets rate_limit to None (the key
            exists but the value is None), it opts out of rate limiting and
            None is returned.

            :returns: The most restrictive rate limit value from the chain,
                or None if no rate limit is set or the node opts out.
        """
        # If this node explicitly sets rate_limit to None, it opts out
        if "rate_limit" in self._metadata and self._metadata["rate_limit"] is None:
            return None

        most_restrictive = None
        current = self
        while current is not None:
            if "rate_limit" in current._metadata:
                limit = current._metadata["rate_limit"]
                if limit is not None:
                    if most_restrictive is None or limit < most_restrictive:
                        most_restrictive = limit
            current = current._parent

        return most_restrictive

    def ancestors(self) -> Iterator[URLNode]:
        """
            Iterate from this node up to the root.

            Yields URLNode instances starting from this node's parent and
            walking up the tree to the root node. The root node is always
            the last node yielded (unless this node is the root, in which
            case nothing is yielded).

            :yields: URLNode instances from parent to root.
        """
        current = self._parent
        while current is not None:
            yield current
            current = current._parent

    def descendants(self) -> Iterator[URLNode]:
        """
            Iterate over all descendants in depth-first order.

            Performs a depth-first traversal of all nodes below this node
            in the tree. Does not include this node itself.

            :yields: URLNode instances that are descendants of this node.
        """
        for child in self._children.values():
            yield child
            yield from child.descendants()




