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

import re
import threading

from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Tuple, TYPE_CHECKING

from ccai.webworks.routing.matcher import Matcher, SegmentType
from ccai.webworks.routing.exceptions import RoutingError

if TYPE_CHECKING:
    from ccai.webworks.endpoints.descriptor import EndpointDescriptor
    from ccai.webworks.endpoints.registry import EndpointRegistry
    from ccai.webworks.routing.request import Request


# Two or more consecutive slashes anywhere in a path.
_REPEATED_SLASHES_RE: re.Pattern = re.compile(r"/{2,}")

# Path segments that never name a route. A request that carries one is
# refused rather than resolved, so a handler never receives a parameter
# that climbs out of the directory it serves. A single-dot segment stays
# where it is and is left to the route that matches it -- a handler may
# redirect such a path to its canonical URL.
_UNROUTABLE_SEGMENTS: Tuple[str, ...] = ("..",)


def canonicalize_path(path: Optional[str]) -> Optional[str]:
    """
        Reduce a request path to the one spelling the router matches.

        A route must be reachable through exactly one path. When the router
        accepts several spellings of a path while another layer -- an access
        policy keyed on the path, an exclusion list -- compares the spelling
        the client sent, the two disagree about which resource a request
        names and the policy is bypassed. Every layer therefore compares the
        canonical path this function returns:

        - the path starts with exactly one ``/``;
        - a run of slashes anywhere in the path is one slash, so
          ``//admin//users`` is ``/admin/users``;
        - one trailing slash is kept, because whether ``/docs/`` and ``/docs``
          are the same route is the router's ``strict_slashes`` decision.

        The function is idempotent.

        :param path: The request path, without the query string.

        :returns: The canonical path, or ``None`` when the path can not name
                  a route: it contains a ``..`` segment or a NUL character.
    """
    rtnval: Optional[str] = None

    candidate = path
    if candidate is None or candidate == "":
        candidate = "/"

    if not candidate.startswith("/"):
        candidate = "/" + candidate

    candidate = _REPEATED_SLASHES_RE.sub("/", candidate)

    routable = True

    if "\x00" in candidate:
        routable = False
    else:
        for segment in candidate.split("/"):
            if segment in _UNROUTABLE_SEGMENTS:
                routable = False
                break

    if routable is True:
        rtnval = candidate

    return rtnval


def remove_dot_segments(canonical_path: str) -> str:
    """
        Remove the ``.`` segments of a canonical path.

        ``/files/./private/x`` and ``/files/private/x`` name the same
        resource to a handler that resolves the path, but they are
        different strings to a policy keyed on the path. A layer that
        decides by path uses this function to find the spelling a request
        should have used, and redirects to it.

        :param canonical_path: A path returned by :func:`canonicalize_path`.

        :returns: The path without ``.`` segments. A trailing ``.`` leaves
                  a trailing slash, as in RFC 3986.
    """
    segments = canonical_path.split("/")
    last_index = len(segments) - 1

    kept: List[str] = []
    for index, segment in enumerate(segments):
        if segment == ".":
            if index == last_index:
                kept.append("")
        else:
            kept.append(segment)

    rtnval = _REPEATED_SLASHES_RE.sub("/", "/".join(kept))

    if rtnval == "":
        rtnval = "/"

    return rtnval


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

        # (route signature, method) -> descriptor, for conflict detection
        # without scanning every registered route.
        self._route_index: Dict[Tuple[str, str], "EndpointDescriptor"] = {}

        # Guards the URL tree. A route is added while holding the lock and
        # a request is matched while holding it, so a request never sees a
        # route that is only partly inserted.
        self._lock = threading.RLock()
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

            The route is added as one step: every method is checked for a
            conflict before any is inserted, and the tree is locked for the
            whole insertion, so a failed registration leaves the router
            unchanged and a concurrent request never matches a route that is
            only partly registered.
            
            :param descriptor: EndpointDescriptor from endpoint-abstractions.
            
            :raises RoutingError: If route conflicts with existing registration,
                or a ``path`` converter is used anywhere but the final segment.
        """
        # Determine the path from descriptor
        path = self._get_descriptor_path(descriptor)
        
        # Create a matcher for the path
        matcher = Matcher(path)

        # A path converter consumes the rest of the request path, so a
        # route that continues after one can never match.
        self._check_wildcard_is_terminal(path, matcher)
        
        # Normalize path for tree insertion (for registration)
        normalized_path = self._normalize_path_for_registration(path)

        signature = self._get_route_signature(path)

        methods_upper = []
        for method in descriptor.methods:
            method_upper = method.upper()
            if method_upper not in methods_upper:
                methods_upper.append(method_upper)

        with self._lock:
            # Check every method for conflicts before inserting any
            for method_upper in methods_upper:
                self._check_conflict(path, method_upper, descriptor)

            for method_upper in methods_upper:
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
                self._route_index[(signature, method_upper)] = descriptor
        
        return

    def _check_wildcard_is_terminal(self, path: str, matcher: Matcher) -> None:
        """
            Refuse a route whose ``path`` converter is not its final segment.

            :param path: The URL path pattern.
            :param matcher: The matcher parsed from the pattern.

            :raises RoutingError: If a wildcard segment is followed by
                another segment.
        """
        segments = matcher.segments

        for segment in segments[:-1]:
            if segment.segment_type == SegmentType.WILDCARD:
                raise RoutingError(
                    f"Invalid route {path}: the path converter '{{{segment.value}:path}}' "
                    f"must be the final segment because it matches the rest of the path",
                    path=path
                )

        return

    def _get_route_signature(self, path: str) -> str:
        """
            Get the form of a route pattern used to detect conflicts.

            Two patterns that match the same requests have the same
            signature. Parameter names do not take part in matching, so
            ``/items/{id}`` and ``/items/{key}`` share the signature
            ``/items/{:str}``; the converter does take part, so
            ``/items/{id:int}`` has the signature ``/items/{:int}``.

            :param path: The URL path pattern.

            :returns: The signature string.
        """
        normalized = self._normalize_path_for_registration(path)
        segments = self._parse_path_segments(normalized)

        parts: List[str] = []

        for segment in segments:
            is_param = segment.startswith("{") and segment.endswith("}")

            if is_param:
                inner = segment[1:-1]
                converter_name = "str"
                if ":" in inner:
                    converter_name = inner.split(":", 1)[1]
                parts.append("{:" + converter_name + "}")
            elif self._case_sensitive:
                parts.append(segment)
            else:
                parts.append(segment.lower())

        rtnval = "/" + "/".join(parts)

        return rtnval
    
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

            Routes conflict when they match the same requests for the same
            method. That is decided on the route signature rather than the
            literal pattern, so two patterns that differ only in the name of
            a parameter are a conflict: the second could never be reached.
            
            :param path: The URL path.
            :param method: The HTTP method.
            :param descriptor: The new descriptor.
            
            :raises RoutingError: If a conflict is detected.
        """
        signature = self._get_route_signature(path)

        existing_desc = self._route_index.get((signature, method))

        if existing_desc is not None:
            existing_name = getattr(existing_desc.handler, "__name__", repr(existing_desc.handler))
            raise RoutingError(
                f"Route conflict: {method} {path} is already registered "
                f"to handler {existing_name}",
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

            The path is matched in its canonical form (see
            :func:`canonicalize_path`), so every spelling of a path reaches
            the same route and a path that has no canonical form matches
            nothing.

            A ``HEAD`` request for a route that only registers ``GET`` is
            matched to the ``GET`` handler; the dispatcher sends the
            response without its body.
            
            :param request: The incoming Request.
            
            :returns: RouteMatch if found, None otherwise.
        """
        rtnval: Optional[RouteMatch] = None

        method = request.method.upper()

        canonical_path = canonicalize_path(request.path)

        if canonical_path is not None:
            with self._lock:
                rtnval = self._match_canonical_path(canonical_path, method)

                if rtnval is None and method == "HEAD":
                    rtnval = self._match_canonical_path(canonical_path, "GET")

        return rtnval

    def _match_canonical_path(self, canonical_path: str, method: str) -> Optional[RouteMatch]:
        """
            Match a canonical path and a method against the URL tree,
            applying the router's trailing slash rule.

            :param canonical_path: The canonical request path.
            :param method: The HTTP method in upper case.

            :returns: RouteMatch if found, None otherwise.
        """
        # Normalize path for matching
        normalized_path = self._normalize_path(canonical_path)
        
        # Try to match against the tree
        match_result = self._match_path(normalized_path, method)
        
        if match_result is not None:
            return match_result
        
        # If strict_slashes is False, try alternate path
        if not self._strict_slashes:
            alt_path = self._get_alternate_slash_path(normalized_path)
            
            match_result = self._match_path(alt_path, method)
            if match_result is not None:
                return match_result
        
        return None

    def _get_alternate_slash_path(self, path: str) -> str:
        """
            Get the path that differs from the given one only by its
            trailing slash.

            :param path: A canonical path.

            :returns: The path without its trailing slash when it has one,
                      otherwise the path with a trailing slash added.
        """
        if path.endswith("/"):
            rtnval = path.rstrip("/") or "/"
        else:
            rtnval = path + "/"

        return rtnval

    def get_redirect_path(self, path: str, method: str) -> Optional[str]:
        """
            Get the path a request should be redirected to because it
            differs from a registered route only by its trailing slash.

            Redirects are produced only when the router was constructed
            with ``redirect_slashes=True``. With ``strict_slashes=False``
            both spellings already match, so there is nothing to redirect.

            :param path: The request path that did not match.
            :param method: The HTTP method of the request.

            :returns: The canonical path of the route that does match, or
                      None when no redirect applies.
        """
        rtnval: Optional[str] = None

        if self._redirect_slashes and self._strict_slashes:
            canonical_path = canonicalize_path(path)

            if canonical_path is not None and canonical_path != "/":
                alt_path = self._get_alternate_slash_path(canonical_path)
                method_upper = method.upper()

                with self._lock:
                    match_result = self._match_path(alt_path, method_upper)

                    if match_result is None and method_upper == "HEAD":
                        match_result = self._match_path(alt_path, "GET")

                if match_result is not None:
                    rtnval = alt_path

        return rtnval

    def get_allowed_methods(self, path: str) -> List[str]:
        """
            Get the list of HTTP methods registered for a given path.

            This method traverses the URL tree to find every node matching
            the given path and returns all HTTP methods that have
            registered handlers at those nodes. If no node matches the
            path, an empty list is returned.

            :param path: The URL path to check.

            :returns: List of HTTP method strings registered for the path.
        """
        methods: List[str] = []

        canonical_path = canonicalize_path(path)

        if canonical_path is not None:
            normalized_path = self._normalize_path(canonical_path)

            with self._lock:
                methods = self._collect_methods_for_path(normalized_path)

                # If strict_slashes is False, try alternate path
                if len(methods) == 0 and not self._strict_slashes:
                    alt_path = self._get_alternate_slash_path(normalized_path)

                    methods = self._collect_methods_for_path(alt_path)

        return methods

    def _collect_methods_for_path(self, path: str) -> List[str]:
        """
            Collect all HTTP methods registered at a path in the URL tree.

            More than one node can match a path -- ``/items/{id}`` and
            ``/items/{key}`` registered for different methods are separate
            nodes -- so the methods of every matching node are combined.

            :param path: Normalized URL path.

            :returns: Sorted list of HTTP method strings.
        """
        segments = self._parse_path_segments(path)

        nodes: List[URLNode] = []
        self._collect_nodes_for_segments(self._root, segments, 0, nodes)

        found = set()
        for node in nodes:
            found.update(node.handlers.keys())

        methods = sorted(found)

        return methods

    def _collect_nodes_for_segments(
        self,
        node: URLNode,
        segments: List[str],
        index: int,
        found: List[URLNode]
    ) -> None:
        """
            Collect every terminal URLNode that matches a sequence of path
            segments, without filtering by HTTP method.

            :param node: Current tree node.
            :param segments: List of path segments.
            :param index: Current segment index.
            :param found: List the matching nodes are appended to.
        """
        # Base case: all segments consumed
        if index >= len(segments):
            if len(node.handlers) > 0 and node not in found:
                found.append(node)
            return

        current_segment = segments[index]
        segment_key = current_segment if self._case_sensitive else current_segment.lower()

        # Static children
        if segment_key in node.children:
            self._collect_nodes_for_segments(
                node.children[segment_key],
                segments,
                index + 1,
                found
            )

        # Parameterized children
        for param_node in node.param_children:
            if param_node.matcher is None:
                continue

            matcher_segments = param_node.matcher.segments
            if matcher_segments and matcher_segments[0].segment_type == SegmentType.WILDCARD:
                remaining_path = "/".join(segments[index:])
                match_result = param_node.matcher.match(f"/{remaining_path}")

                if match_result is not None:
                    if len(param_node.handlers) > 0 and param_node not in found:
                        found.append(param_node)
                continue

            match_result = param_node.matcher.match(f"/{current_segment}")

            if match_result is not None:
                self._collect_nodes_for_segments(
                    param_node,
                    segments,
                    index + 1,
                    found
                )

        return

    
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
