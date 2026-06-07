"""
    URL Router for matching requests to endpoint handlers.
    
    This module provides the Router class that builds an efficient URL
    matching tree from EndpointDescriptors and matches incoming requests
    to the appropriate handlers.
    
    The router supports:
    - Static path segments (exact match)
    - Parameterized segments with type converters
    - Wildcard segments for catch-all routes
    - Configurable trailing slash handling
    - Case-sensitive or case-insensitive matching
    
    Example:
        router = Router()
        router.add_endpoint(descriptor)
        
        match = router.match(request)
        if match is not None:
            response = match.handler(request)
"""

from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Tuple, TYPE_CHECKING

from ccai.webworks.routing.matcher import Matcher, SegmentType
from ccai.webworks.routing.exceptions import RoutingError

if TYPE_CHECKING:
    from ccai.webworks.endpoints.descriptor import EndpointDescriptor
    from ccai.webworks.endpoints.registry import EndpointRegistry
    from ccai.webworks.routing.request import Request


@dataclass
class RouteMatch:
    """
        Result of a successful route match containing all information
        needed to dispatch the request.
        
        :param handler: The callable endpoint handler.
        :param path_params: Dictionary of extracted path parameters.
        :param descriptor: The EndpointDescriptor for accessing metadata.
        :param matched_path: The URL pattern that matched.
    """
    
    handler: Callable
    path_params: Dict[str, Any]
    descriptor: "EndpointDescriptor"
    matched_path: str


@dataclass
class URLNode:
    """
        Node in the URL matching tree.
        
        Each node represents a path segment and can have children
        for subsequent segments. Handlers are stored at nodes where
        routes terminate.
        
        :param segment: Static segment value or parameter pattern.
        :param is_param: True if this is a parameterized segment.
        :param param_name: Name of the parameter (if parameterized).
        :param matcher: Matcher for this segment (if parameterized).
        :param children: Child nodes keyed by segment value.
        :param param_children: Parameterized child nodes (ordered by specificity).
        :param handlers: Handlers keyed by HTTP method.
    """
    
    segment: str = ""
    is_param: bool = False
    param_name: Optional[str] = None
    matcher: Optional[Matcher] = None
    children: Dict[str, "URLNode"] = field(default_factory=dict)
    param_children: List["URLNode"] = field(default_factory=list)
    handlers: Dict[str, Tuple[Callable, "EndpointDescriptor", str]] = field(default_factory=dict)
    # handlers value: (handler, descriptor, matched_path)


class Router:
    """
        URL router that matches requests to endpoint handlers.
        
        The Router builds an efficient URL tree from registered
        EndpointDescriptors and provides O(path_depth) matching
        for incoming requests.
        
        Configuration options:
        - strict_slashes: If True, /path and /path/ are different routes.
        - case_sensitive: If True, paths are matched case-sensitively.
        - redirect_slashes: If True, redirect on trailing slash mismatch.
        
        Example:
            router = Router(strict_slashes=False)
            router.add_endpoint(descriptor)
            
            match = router.match(request)
            if match is not None:
                handler = match.handler
                params = match.path_params
    """
    
    def __init__(
        self,
        strict_slashes: bool = True,
        case_sensitive: bool = True,
        redirect_slashes: bool = False
    ):
        """
            Construct a Router.
            
            :param strict_slashes: If True, /path and /path/ are different routes.
            :param case_sensitive: If True, paths are matched case-sensitively.
            :param redirect_slashes: If True, redirect on trailing slash mismatch.
        """
        self._strict_slashes = strict_slashes
        self._case_sensitive = case_sensitive
        self._redirect_slashes = redirect_slashes
        self._root = URLNode()
        self._routes: List[Tuple[str, str, "EndpointDescriptor"]] = []  # (path, method, descriptor)
        return
    
    @property
    def strict_slashes(self) -> bool:
        """
            Whether trailing slashes are significant.
            
            :returns: True if /path and /path/ are different routes.
        """
        return self._strict_slashes
    
    @property
    def case_sensitive(self) -> bool:
        """
            Whether path matching is case-sensitive.
            
            :returns: True if paths are matched case-sensitively.
        """
        return self._case_sensitive
    
    @property
    def redirect_slashes(self) -> bool:
        """
            Whether to redirect on trailing slash mismatch.
            
            :returns: True if redirects are enabled.
        """
        return self._redirect_slashes

    
    def add_endpoint(self, descriptor: "EndpointDescriptor") -> None:
        """
            Add an endpoint descriptor to the router.
            
            This method parses the endpoint's path pattern and adds it
            to the URL tree. Each HTTP method supported by the endpoint
            is registered separately.
            
            :param descriptor: EndpointDescriptor from endpoint-abstractions.
            
            :raises RoutingError: If route conflicts with existing registration.
        """
        # Determine the path from descriptor
        path = self._get_descriptor_path(descriptor)
        
        # Create a matcher for the path
        matcher = Matcher(path)
        
        # Normalize path for tree insertion (for registration)
        normalized_path = self._normalize_path_for_registration(path)
        
        # Add route for each HTTP method
        for method in descriptor.methods:
            method_upper = method.upper()
            
            # Check for conflicts
            self._check_conflict(path, method_upper, descriptor)
            
            # Insert into tree
            self._insert_route(
                normalized_path,
                method_upper,
                descriptor.handler,
                descriptor,
                path,
                matcher
            )
            
            # Track the route
            self._routes.append((path, method_upper, descriptor))
        
        return
    
    def _get_descriptor_path(self, descriptor: "EndpointDescriptor") -> str:
        """
            Get the URL path from a descriptor.
            
            :param descriptor: The endpoint descriptor.
            
            :returns: The URL path string.
        """
        if descriptor.path is not None:
            return descriptor.path
        elif descriptor.leaf is not None:
            return f"/{descriptor.leaf}"
        else:
            return "/"
    
    def _normalize_path_for_registration(self, path: str) -> str:
        """
            Normalize a path for registration (conflict checking).
            
            :param path: The path to normalize.
            
            :returns: Normalized path string.
        """
        # Handle trailing slashes for registration
        if not self._strict_slashes:
            path = path.rstrip("/")
            if not path:
                path = "/"
        
        return path
    
    def _normalize_path(self, path: str) -> str:
        """
            Normalize a path for matching.
            
            :param path: The path to normalize.
            
            :returns: Normalized path string.
        """
        # When strict_slashes is True, don't normalize trailing slashes
        # When strict_slashes is False, strip trailing slashes for matching
        if not self._strict_slashes:
            path = path.rstrip("/")
            if not path:
                path = "/"
        
        return path
    
    def _check_conflict(
        self,
        path: str,
        method: str,
        descriptor: "EndpointDescriptor"
    ) -> None:
        """
            Check if a route conflicts with an existing registration.
            
            :param path: The URL path.
            :param method: The HTTP method.
            :param descriptor: The new descriptor.
            
            :raises RoutingError: If a conflict is detected.
        """
        normalized = self._normalize_path_for_registration(path)
        
        for existing_path, existing_method, existing_desc in self._routes:
            existing_normalized = self._normalize_path_for_registration(existing_path)
            
            if existing_normalized == normalized and existing_method == method:
                raise RoutingError(
                    f"Route conflict: {method} {path} is already registered "
                    f"to handler {existing_desc.handler.__name__}",
                    path=path,
                    method=method,
                    existing_handler=existing_desc.handler
                )
        
        return
    
    def _insert_route(
        self,
        path: str,
        method: str,
        handler: Callable,
        descriptor: "EndpointDescriptor",
        original_path: str,
        matcher: Matcher
    ) -> None:
        """
            Insert a route into the URL tree.
            
            :param path: Normalized URL path.
            :param method: HTTP method.
            :param handler: Handler callable.
            :param descriptor: Endpoint descriptor.
            :param original_path: Original path pattern.
            :param matcher: Matcher for the path.
        """
        # Parse path into segments
        segments = self._parse_path_segments(path)
        
        # Navigate/create tree nodes
        current = self._root
        
        for i, segment in enumerate(segments):
            is_param = segment.startswith("{") and segment.endswith("}")
            
            if is_param:
                # Parameterized segment
                current = self._get_or_create_param_node(current, segment, matcher, i)
            else:
                # Static segment
                segment_key = segment if self._case_sensitive else segment.lower()
                
                if segment_key not in current.children:
                    current.children[segment_key] = URLNode(segment=segment)
                
                current = current.children[segment_key]
        
        # Register handler at terminal node
        current.handlers[method] = (handler, descriptor, original_path)
        
        return
    
    def _parse_path_segments(self, path: str) -> List[str]:
        """
            Parse a path into segments.
            
            :param path: The URL path.
            
            :returns: List of path segments.
        """
        # Track if path has trailing slash for strict_slashes handling
        has_trailing_slash = path.endswith("/") and len(path) > 1
        
        normalized = path.strip("/")
        if not normalized:
            return []
        
        segments = normalized.split("/")
        
        # If strict_slashes is True and path has trailing slash,
        # add an empty segment marker to differentiate
        if self._strict_slashes and has_trailing_slash:
            segments.append("")
        
        return segments
    
    def _get_or_create_param_node(
        self,
        parent: URLNode,
        segment: str,
        matcher: Matcher,
        segment_index: int
    ) -> URLNode:
        """
            Get or create a parameterized node.
            
            :param parent: Parent node.
            :param segment: Parameter segment (e.g., "{id:int}").
            :param matcher: Matcher for the full path.
            :param segment_index: Index of this segment in the path.
            
            :returns: The parameterized node.
        """
        # Extract parameter name from segment
        param_name = segment[1:-1]  # Remove { and }
        if ":" in param_name:
            param_name = param_name.split(":")[0]
        
        # Check if we already have a node for this parameter pattern
        for child in parent.param_children:
            if child.segment == segment:
                return child
        
        # Create new parameterized node
        # Create a matcher just for this segment
        segment_matcher = Matcher(f"/{segment}")
        
        node = URLNode(
            segment=segment,
            is_param=True,
            param_name=param_name,
            matcher=segment_matcher
        )
        
        # Insert in order of specificity (more specific first)
        # Static > typed param > string param > wildcard
        inserted = False
        for i, existing in enumerate(parent.param_children):
            if segment_matcher.specificity > existing.matcher.specificity:
                parent.param_children.insert(i, node)
                inserted = True
                break
        
        if not inserted:
            parent.param_children.append(node)
        
        return node

    
    def load_from_registry(self, registry: "EndpointRegistry") -> None:
        """
            Bulk-load all descriptors from an EndpointRegistry.
            
            This method collects all registered descriptors from the
            registry and adds them to the router.
            
            :param registry: EndpointRegistry to load from.
        """
        descriptors = registry.collect()
        
        for descriptor in descriptors:
            self.add_endpoint(descriptor)
        
        return

    
    def match(self, request: "Request") -> Optional[RouteMatch]:
        """
            Match a request to a registered route.
            
            This method traverses the URL tree to find a matching route
            for the request's path and method. If found, it returns a
            RouteMatch containing the handler, path parameters, and
            descriptor.
            
            :param request: The incoming Request.
            
            :returns: RouteMatch if found, None otherwise.
        """
        path = request.path
        method = request.method.upper()
        
        # Normalize path for matching
        normalized_path = self._normalize_path(path)
        
        # Try to match against the tree
        match_result = self._match_path(normalized_path, method)
        
        if match_result is not None:
            return match_result
        
        # If strict_slashes is False, try alternate path
        if not self._strict_slashes:
            if normalized_path.endswith("/"):
                alt_path = normalized_path.rstrip("/") or "/"
            else:
                alt_path = normalized_path + "/"
            
            match_result = self._match_path(alt_path, method)
            if match_result is not None:
                return match_result
        
        return None

    def get_allowed_methods(self, path: str) -> List[str]:
        """
            Get the list of HTTP methods registered for a given path.

            This method traverses the URL tree to find a node matching
            the given path and returns all HTTP methods that have
            registered handlers at that node. If no node matches the
            path, an empty list is returned.

            :param path: The URL path to check.

            :returns: List of HTTP method strings registered for the path.
        """
        normalized_path = self._normalize_path(path)

        methods = self._collect_methods_for_path(normalized_path)

        if len(methods) > 0:
            return methods

        # If strict_slashes is False, try alternate path
        if not self._strict_slashes:
            if normalized_path.endswith("/"):
                alt_path = normalized_path.rstrip("/") or "/"
            else:
                alt_path = normalized_path + "/"

            methods = self._collect_methods_for_path(alt_path)

        return methods

    def _collect_methods_for_path(self, path: str) -> List[str]:
        """
            Collect all HTTP methods registered at a path in the URL tree.

            :param path: Normalized URL path.

            :returns: List of HTTP method strings.
        """
        segments = self._parse_path_segments(path)

        node = self._find_node_for_segments(self._root, segments, 0)

        if node is None:
            return []

        methods = sorted(node.handlers.keys())

        return methods

    def _find_node_for_segments(
        self,
        node: URLNode,
        segments: List[str],
        index: int
    ) -> Optional[URLNode]:
        """
            Find the terminal URLNode for a sequence of path segments.

            This method traverses the URL tree without filtering by
            HTTP method, returning the node where handlers are registered
            for the given path.

            :param node: Current tree node.
            :param segments: List of path segments.
            :param index: Current segment index.

            :returns: The terminal URLNode if found, None otherwise.
        """
        # Base case: all segments consumed
        if index >= len(segments):
            if len(node.handlers) > 0:
                return node
            return None

        current_segment = segments[index]
        segment_key = current_segment if self._case_sensitive else current_segment.lower()

        # Try static children first (more specific)
        if segment_key in node.children:
            result = self._find_node_for_segments(
                node.children[segment_key],
                segments,
                index + 1
            )
            if result is not None:
                return result

        # Try case-insensitive match if needed
        if not self._case_sensitive:
            for child_key, child_node in node.children.items():
                if child_key.lower() == segment_key.lower():
                    result = self._find_node_for_segments(
                        child_node,
                        segments,
                        index + 1
                    )
                    if result is not None:
                        return result

        # Try parameterized children (in order of specificity)
        for param_node in node.param_children:
            # Check if this is a wildcard (path converter)
            if param_node.matcher is not None:
                matcher_segments = param_node.matcher.segments
                if matcher_segments and matcher_segments[0].segment_type == SegmentType.WILDCARD:
                    remaining_path = "/".join(segments[index:])
                    match_result = param_node.matcher.match(f"/{remaining_path}")

                    if match_result is not None:
                        if len(param_node.handlers) > 0:
                            return param_node
                    continue

            # Regular parameterized segment
            if param_node.matcher is not None:
                match_result = param_node.matcher.match(f"/{current_segment}")

                if match_result is not None:
                    result = self._find_node_for_segments(
                        param_node,
                        segments,
                        index + 1
                    )
                    if result is not None:
                        return result

        return None

    
    def _match_path(self, path: str, method: str) -> Optional[RouteMatch]:
        """
            Match a path against the URL tree.
            
            :param path: Normalized URL path.
            :param method: HTTP method.
            
            :returns: RouteMatch if found, None otherwise.
        """
        segments = self._parse_path_segments(path)
        
        # Try to match using the tree
        result = self._match_segments(self._root, segments, 0, {}, method)
        
        return result
    
    def _match_segments(
        self,
        node: URLNode,
        segments: List[str],
        index: int,
        params: Dict[str, Any],
        method: str
    ) -> Optional[RouteMatch]:
        """
            Recursively match path segments against the tree.
            
            :param node: Current tree node.
            :param segments: List of path segments.
            :param index: Current segment index.
            :param params: Accumulated path parameters.
            :param method: HTTP method.
            
            :returns: RouteMatch if found, None otherwise.
        """
        # Base case: all segments consumed
        if index >= len(segments):
            # Check if this node has a handler for the method
            if method in node.handlers:
                handler, descriptor, matched_path = node.handlers[method]
                return RouteMatch(
                    handler=handler,
                    path_params=params.copy(),
                    descriptor=descriptor,
                    matched_path=matched_path
                )
            return None
        
        current_segment = segments[index]
        segment_key = current_segment if self._case_sensitive else current_segment.lower()
        
        # Try static children first (more specific)
        if segment_key in node.children:
            result = self._match_segments(
                node.children[segment_key],
                segments,
                index + 1,
                params,
                method
            )
            if result is not None:
                return result
        
        # Try case-insensitive match if needed
        if not self._case_sensitive:
            for child_key, child_node in node.children.items():
                if child_key.lower() == segment_key.lower():
                    result = self._match_segments(
                        child_node,
                        segments,
                        index + 1,
                        params,
                        method
                    )
                    if result is not None:
                        return result
        
        # Try parameterized children (in order of specificity)
        for param_node in node.param_children:
            # Check if this is a wildcard (path converter)
            if param_node.matcher is not None:
                matcher_segments = param_node.matcher.segments
                if matcher_segments and matcher_segments[0].segment_type == SegmentType.WILDCARD:
                    # Wildcard matches remaining path
                    remaining_path = "/".join(segments[index:])
                    match_result = param_node.matcher.match(f"/{remaining_path}")
                    
                    if match_result is not None:
                        new_params = params.copy()
                        new_params.update(match_result)
                        
                        # Check if this node has a handler
                        if method in param_node.handlers:
                            handler, descriptor, matched_path = param_node.handlers[method]
                            return RouteMatch(
                                handler=handler,
                                path_params=new_params,
                                descriptor=descriptor,
                                matched_path=matched_path
                            )
                    continue
            
            # Regular parameterized segment
            if param_node.matcher is not None:
                match_result = param_node.matcher.match(f"/{current_segment}")
                
                if match_result is not None:
                    new_params = params.copy()
                    new_params.update(match_result)
                    
                    result = self._match_segments(
                        param_node,
                        segments,
                        index + 1,
                        new_params,
                        method
                    )
                    if result is not None:
                        return result
        
        return None
    
    def __repr__(self) -> str:
        """
            Return string representation of the Router.
            
            :returns: String representation.
        """
        route_count = len(self._routes)
        return f"Router(routes={route_count}, strict_slashes={self._strict_slashes})"
