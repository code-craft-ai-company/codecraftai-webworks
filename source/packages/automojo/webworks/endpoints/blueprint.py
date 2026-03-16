"""
.. module:: blueprint
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: Blueprint class for grouping related endpoints under a shared parent path.

.. moduleauthor:: Automation Mojo LLC
"""

__author__ = "Automation Mojo LLC"
__copyright__ = "Copyright 2025, Automation Mojo LLC"
__credits__ = []

from dataclasses import dataclass
from typing import Any, Callable, Dict, List, Optional, Protocol, Type, TypeVar

from automojo.webworks.endpoints.accesspolicy import AccessPolicy
from automojo.webworks.endpoints.constraints import EndpointConstraints
from automojo.webworks.endpoints.descriptor import EndpointDescriptor
from automojo.webworks.endpoints.doc import Doc
from automojo.webworks.endpoints.endpoint import Endpoint
from automojo.webworks.endpoints.exceptions import EndpointRegistrationError
from automojo.webworks.endpoints.merging import ConstraintMerger
from automojo.webworks.endpoints.ratelimit import RateLimit
from automojo.webworks.endpoints.registry import EndpointRegistry


# Type variable for preserving function signatures in decorators
F = TypeVar("F", bound=Callable[..., Any])


@dataclass
class BlueprintConfig:
    """
        Configuration options for blueprint behavior.
        
        This dataclass provides a structured way to configure blueprint
        settings including path composition and constraint merge behaviors.
        
        Attributes:
            base_path: Base URL path for all child endpoints.
            base_leaf: Base URL leaf segment (alternative to base_path).
            merge_tags: If True, parent tags are appended to child tags.
            replace_tags: If True, child tags fully replace parent tags.
            replace_scopes: If True, child scopes replace parent scopes.
            replace_roles: If True, child roles replace parent roles.
    """
    
    base_path: Optional[str] = None
    base_leaf: Optional[str] = None
    merge_tags: bool = False
    replace_tags: bool = False
    replace_scopes: bool = False
    replace_roles: bool = False


class Router(Protocol):
    """
        Protocol defining the minimal router interface for endpoint
        registration.
    """
    
    def add_endpoint(self, descriptor: EndpointDescriptor) -> None:
        """
            Add an endpoint descriptor to the router.
            
            :param descriptor: The EndpointDescriptor to add.
        """
        ...


class Blueprint(Endpoint):
    """
        Endpoint composite that emits multiple attachments in one declaration.
        
        Blueprint provides a shared parent path and constraint inheritance for
        grouped endpoints. It derives from Endpoint and calls attach_at for
        each child endpoint relative to a shared parent path.
        
        Subclasses should define child endpoints by decorating methods with
        attach_at or by overriding the register() method to manually attach
        child endpoints.
        
        Class Attributes:
            base_path: Base URL path for all child endpoints.
            base_leaf: Base URL leaf segment (alternative to base_path).
            merge_tags: If True, parent tags are appended to child tags.
            replace_scopes: If True, child scopes replace parent scopes.
            replace_roles: If True, child roles replace parent roles.
    """
    
    # Blueprint-specific attributes for path composition
    base_path: Optional[str] = None
    base_leaf: Optional[str] = None
    
    # Merge behavior flags
    merge_tags: bool = False
    replace_scopes: bool = False
    replace_roles: bool = False
    
    # Internal tracking of registered descriptors per blueprint class
    # This is a dict keyed by class name to avoid sharing across subclasses
    _blueprint_descriptors: Dict[str, List[EndpointDescriptor]] = {}
    
    # Legacy storage for child descriptors registered via attach_at
    _child_descriptors: List[EndpointDescriptor] = []
    
    @classmethod
    def register(
        cls,
        router: Optional[Router] = None
    ) -> List[EndpointDescriptor]:
        """
            Register all child endpoints and return their descriptors.
            
            This method collects all endpoint descriptors that have been
            registered via attach_at on this blueprint class. If a router
            is provided, each descriptor is also added to the router.
            
            The method is idempotent - calling it multiple times returns
            the same descriptors. If re-registration is needed, the
            internal cache is cleared and descriptors are re-collected.
            
            Subclasses can override this method to implement custom
            registration logic.
            
            :param router: Optional router to add endpoints to. If None,
                          descriptors are returned without router registration.
            
            :returns: List of EndpointDescriptor objects for all registered endpoints.
            
            Requirements: 1.4, 1.5, 1.6, 6.7
        """
        # Get the class key for tracking descriptors per blueprint class
        class_key = cls._get_class_key()
        
        # Check if we already have cached descriptors (idempotency)
        if class_key in cls._blueprint_descriptors:
            cached_descriptors = cls._blueprint_descriptors[class_key]
            
            # If router is provided, add each cached descriptor to it
            if router is not None:
                for descriptor in cached_descriptors:
                    router.add_endpoint(descriptor)
            
            return cached_descriptors.copy()
        
        # Collect descriptors from the registry that belong to this blueprint
        all_descriptors = EndpointRegistry.collect()
        
        # Filter to descriptors that were registered by this blueprint class
        blueprint_descriptors = cls._collect_blueprint_descriptors(all_descriptors)
        
        # Cache the descriptors for idempotency
        cls._blueprint_descriptors[class_key] = blueprint_descriptors
        
        # If router is provided, add each descriptor to it
        if router is not None:
            for descriptor in blueprint_descriptors:
                router.add_endpoint(descriptor)
        
        return blueprint_descriptors.copy()
    
    @classmethod
    def _get_class_key(cls) -> str:
        """
            Get a unique key for this blueprint class.
            
            This key is used to track registered descriptors per blueprint
            class, ensuring that subclasses don't share descriptor caches.
            
            :returns: A unique string key for this class.
        """
        return f"{cls.__module__}.{cls.__name__}"
    
    @classmethod
    def clear_registration(cls) -> None:
        """
            Clear the cached registration for this blueprint.
            
            This method clears the internal descriptor cache, allowing
            the next call to register() to re-collect descriptors.
            This is useful for testing or when the blueprint's endpoints
            have changed.
        """
        class_key = cls._get_class_key()
        if class_key in cls._blueprint_descriptors:
            del cls._blueprint_descriptors[class_key]
    
    @classmethod
    def _collect_blueprint_descriptors(
        cls,
        all_descriptors: List[EndpointDescriptor]
    ) -> List[EndpointDescriptor]:
        """
            Collect descriptors that belong to this blueprint.
            
            This method filters the global descriptor list to find those
            that were registered by this blueprint class.
            
            :param all_descriptors: All registered descriptors.
            
            :returns: List of descriptors belonging to this blueprint.
        """
        blueprint_descriptors = []
        base = cls._get_base_path()
        
        for descriptor in all_descriptors:
            # Check if descriptor's path starts with our base path
            desc_path = descriptor.path
            if desc_path is None and descriptor.leaf is not None:
                desc_path = f"/{descriptor.leaf}"
            
            if desc_path is not None and base is not None:
                if desc_path.startswith(base):
                    blueprint_descriptors.append(descriptor)
            elif base is None:
                # No base path - include all descriptors from our module
                if descriptor.module == cls.__module__:
                    blueprint_descriptors.append(descriptor)
        
        return blueprint_descriptors
    
    @classmethod
    def _get_base_path(cls) -> Optional[str]:
        """
            Get the base path for this blueprint.
            
            :returns: The base path string, or None if not set.
        """
        if cls.base_path is not None:
            return cls.base_path.rstrip("/")
        elif cls.base_leaf is not None:
            return f"/{cls.base_leaf}"
        return None
    
    @classmethod
    def _compose_path(cls, leaf: Optional[str], path: Optional[str]) -> str:
        """
            Compose the full path from base_path/base_leaf and child leaf/path.
            
            This method computes the final URL path by combining the blueprint's
            base path with the child's leaf or path. It handles:
            - Absolute path override (child path starting with / overrides composition)
            - Path normalization (removes duplicate slashes)
            - Base path composition with leaf segments
            
            :param leaf: Child leaf segment.
            :param path: Child full path (if provided, may override composition).
            
            :returns: Composed full path string.
            
            :raises ValueError: If neither leaf nor path is provided and no base exists.
        """
        base = cls._get_base_path()
        
        # Handle case where child provides an absolute path that should override
        # If path starts with / and we have no base, use it directly
        if path is not None:
            # Normalize the path - remove leading/trailing whitespace
            path = path.strip()
            
            if base is None:
                # No base path - use child path directly
                if not path.startswith("/"):
                    return f"/{path}"
                return path
            
            # Compose base with child path
            if path.startswith("/"):
                # Absolute child path - append to base
                composed = f"{base}{path}"
            else:
                # Relative child path
                composed = f"{base}/{path}"
            
            # Normalize double slashes
            while "//" in composed:
                composed = composed.replace("//", "/")
            
            return composed
        
        if leaf is not None:
            # Normalize the leaf - remove leading/trailing whitespace and slashes
            leaf = leaf.strip().strip("/")
            
            if base is None:
                # No base path - construct from leaf
                return f"/{leaf}"
            
            # Compose base with leaf
            composed = f"{base}/{leaf}"
            
            # Normalize double slashes
            while "//" in composed:
                composed = composed.replace("//", "/")
            
            return composed
        
        # Neither leaf nor path provided
        if base is not None:
            return base
        
        # No base, no leaf, no path - return root
        return "/"
    
    @classmethod
    def _merge_constraints(
        cls,
        child_kwargs: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
            Merge parent constraints with child kwargs following inheritance rules.
            
            This method uses the ConstraintMerger utilities to merge:
            - Access policies (roles, scopes, authentication requirements)
            - Rate limits (most restrictive wins)
            - Tags (merge, replace, or child-wins behaviors)
            
            The merge behavior is controlled by the blueprint's flags:
            - merge_tags: If True, parent tags are appended to child tags
            - replace_scopes: If True, child scopes replace parent scopes
            - replace_roles: If True, child roles replace parent roles
            
            :param child_kwargs: Kwargs provided to attach_at.
            
            :returns: Merged kwargs with inherited values filled in.
        """
        merged = dict(child_kwargs)
        
        # Merge access policies
        child_access_policy = child_kwargs.get("access_policy")
        merged_access_policy = ConstraintMerger.merge_access_policies(
            parent=cls.access_policy,
            child=child_access_policy,
            replace_roles=cls.replace_roles,
            replace_scopes=cls.replace_scopes
        )
        merged["access_policy"] = merged_access_policy
        
        # Merge rate limits
        child_rate_limit = child_kwargs.get("rate_limit")
        merged_rate_limit = ConstraintMerger.merge_rate_limits(
            parent=cls.rate_limit,
            child=child_rate_limit
        )
        merged["rate_limit"] = merged_rate_limit
        
        # Merge tags
        child_tags = child_kwargs.get("tags")
        parent_tags = list(cls.tags) if cls.tags else []
        child_tags_list = list(child_tags) if child_tags else []
        merged_tags = ConstraintMerger.merge_tags(
            parent=parent_tags,
            child=child_tags_list,
            merge=cls.merge_tags,
            replace=False  # replace is handled by child_tags being set
        )
        merged["tags"] = merged_tags if merged_tags else None
        
        # Merge version (child overrides parent)
        if "version" not in child_kwargs or child_kwargs.get("version") is None:
            merged["version"] = cls.version
        
        # Merge methods (child overrides parent)
        if "methods" not in child_kwargs or child_kwargs.get("methods") is None:
            merged["methods"] = list(cls.methods) if cls.methods else ["GET"]
        
        return merged
    
    @classmethod
    def attach_at(
        cls,
        leaf: Optional[str] = None,
        path: Optional[str] = None,
        methods: Optional[List[str]] = None,
        version: Optional[str] = None,
        tags: Optional[List[str]] = None,
        access_policy: Optional[AccessPolicy] = None,
        rate_limit: Optional[RateLimit] = None,
        request_schema: Optional[Type] = None,
        response_schema: Optional[Type] = None,
        error_map: Optional[Dict[int, Type]] = None,
        doc: Optional[Doc] = None,
        on_conflict: str = "error",
        **extras
    ) -> Callable[[F], F]:
        """
            Decorator that binds a handler to a URL location relative to the blueprint's base.
            
            This method overrides Endpoint.attach_at to:
            1. Validate mandatory metadata (leaf or path required)
            2. Compose paths using _compose_path() relative to blueprint base
            3. Merge constraints using _merge_constraints() for inheritance
            4. Call parent attach_at with merged values
            
            The decorator returns the original function unchanged, allowing
            decorator stacking to work correctly.
            
            :param leaf: URL leaf segment (relative to blueprint base).
            :param path: Full URL path (relative to blueprint base).
            :param methods: HTTP methods (defaults to class attribute).
            :param version: API version string.
            :param tags: Documentation tags.
            :param access_policy: Security policy (defaults to class attribute).
            :param rate_limit: Rate limiting config (defaults to class attribute).
            :param request_schema: Request body schema (dataclass or Pydantic).
            :param response_schema: Response body schema.
            :param error_map: Mapping of status codes to error schemas.
            :param doc: Documentation object with summary/description.
            :param on_conflict: "error" to raise on conflict, "replace" to override.
            :param extras: Additional kwargs stored in descriptor.extras.
            
            :returns: Decorator that returns the original function unchanged.
            
            :raises EndpointRegistrationError: If mandatory metadata missing.
            :raises EndpointConflictError: If path+method conflicts with existing.
        """
        # Step 1: Validate mandatory metadata
        # Either leaf or path must be provided (Requirement 3.4)
        if leaf is None and path is None:
            raise EndpointRegistrationError(
                message="Either 'leaf' or 'path' must be provided to attach_at()",
                endpoint=cls,
                missing_fields=["leaf", "path"]
            )
        
        # Step 2: Compose path using _compose_path()
        # This handles base_path/base_leaf composition with child leaf/path
        computed_path = cls._compose_path(leaf=leaf, path=path)
        
        # Step 3: Build child kwargs dict for constraint merging
        child_kwargs: Dict[str, Any] = {
            "methods": methods,
            "version": version,
            "tags": tags,
            "access_policy": access_policy,
            "rate_limit": rate_limit,
        }
        
        # Step 4: Merge constraints using _merge_constraints()
        # This applies inheritance rules for access_policy, rate_limit, tags, etc.
        merged = cls._merge_constraints(child_kwargs)
        
        # Step 5: Call parent attach_at with merged values
        # Pass computed_path as path (leaf is None since we computed full path)
        return super().attach_at(
            leaf=None,  # We use computed path instead
            path=computed_path,
            methods=merged.get("methods"),
            version=merged.get("version"),
            tags=merged.get("tags"),
            access_policy=merged.get("access_policy"),
            rate_limit=merged.get("rate_limit"),
            request_schema=request_schema,
            response_schema=response_schema,
            error_map=error_map,
            doc=doc,
            on_conflict=on_conflict,
            **extras
        )
    
    @classmethod
    def _compute_full_path(
        cls,
        leaf: Optional[str],
        path: Optional[str]
    ) -> Optional[str]:
        """
            Compute the full path for an endpoint relative to blueprint base.
            
            :param leaf: The endpoint's leaf segment.
            :param path: The endpoint's path.
            
            :returns: The computed full path, or None if no path can be computed.
        """
        base = cls._get_base_path()
        
        if base is None:
            # No base path - return path or construct from leaf
            if path is not None:
                return path
            elif leaf is not None:
                return f"/{leaf}"
            return None
        
        # Compute path relative to base
        if path is not None:
            if path.startswith("/"):
                # Absolute path - append to base
                return f"{base}{path}"
            else:
                # Relative path
                return f"{base}/{path}"
        elif leaf is not None:
            return f"{base}/{leaf}"
        else:
            return base
    
    @classmethod
    def _merge_blueprint_tags(
        cls,
        child_tags: Optional[List[str]]
    ) -> Optional[List[str]]:
        """
            Merge child tags with blueprint tags according to merge_tags setting.
            
            :param child_tags: Tags specified for the child endpoint.
            
            :returns: Merged tags list, or None if no tags.
        """
        if not cls.merge_tags:
            # Default behavior: child tags win
            if child_tags is not None:
                return child_tags
            elif cls.tags:
                return list(cls.tags)
            return None
        
        # merge_tags=True: append parent tags to child tags
        result = list(child_tags) if child_tags else []
        
        for tag in cls.tags:
            if tag not in result:
                result.append(tag)
        
        return result if result else None
    
    @classmethod
    def attach_child(
        cls,
        child_endpoint: Type["Endpoint"],
        leaf: Optional[str] = None,
        path: Optional[str] = None,
        methods: Optional[List[str]] = None,
        version: Optional[str] = None,
        tags: Optional[List[str]] = None,
        access_policy: Optional[AccessPolicy] = None,
        rate_limit: Optional[RateLimit] = None,
        **kwargs
    ) -> EndpointDescriptor:
        """
            Attach a child endpoint relative to this blueprint's base path.
            
            This method creates a descriptor for the child endpoint with
            paths computed relative to the parent's base_path/base_leaf.
            Constraints are merged following blueprint inheritance rules
            using the ConstraintMerger utilities.
            
            The method preserves child class attributes when overrides are
            not provided, and applies overrides only to specified attributes.
            
            :param child_endpoint: The child endpoint class to attach.
            :param leaf: Override for child's leaf (relative to parent base).
            :param path: Override for child's path (relative to parent base).
            :param methods: Override for child's methods.
            :param version: Override for child's version.
            :param tags: Override for child's tags.
            :param access_policy: Override for child's access policy.
            :param rate_limit: Override for child's rate limit.
            :param kwargs: Additional overrides for child descriptor.
            
            :returns: The merged EndpointDescriptor for the child.
            
            Requirements: 4.2, 4.3, 4.5, 4.6, 6.5, 6.6
        """
        # Step 1: Determine child's leaf/path
        # Use override if provided, otherwise use child's class attribute
        child_leaf = leaf if leaf is not None else getattr(child_endpoint, "base_leaf", None)
        if child_leaf is None:
            child_leaf = getattr(child_endpoint, "leaf", None)
        
        child_path = path if path is not None else getattr(child_endpoint, "base_path", None)
        if child_path is None:
            child_path = getattr(child_endpoint, "path", None)
        
        # Step 2: Compose path relative to parent base_path/base_leaf
        # This handles the path composition per Requirements 4.3, 4.4
        composed_path = cls._compose_path(leaf=child_leaf, path=child_path)
        
        # Step 3: Determine child's methods
        # Use override if provided, otherwise use child's class attribute
        child_methods = methods if methods is not None else list(child_endpoint.methods)
        
        # Step 4: Determine child's version
        # Use override if provided, otherwise use child's class attribute
        # If child doesn't have version, inherit from parent
        child_version = version
        if child_version is None:
            child_version = getattr(child_endpoint, "version", None)
        if child_version is None:
            child_version = cls.version
        
        # Step 5: Merge tags using ConstraintMerger
        # Use override if provided, otherwise use child's class attribute
        child_tags_list = tags if tags is not None else list(child_endpoint.tags)
        parent_tags_list = list(cls.tags) if cls.tags else []
        
        merged_tags = ConstraintMerger.merge_tags(
            parent=parent_tags_list,
            child=child_tags_list,
            merge=cls.merge_tags,
            replace=False  # Child tags win by default unless merge_tags=True
        )
        
        # Step 6: Merge access policies using ConstraintMerger
        # Use override if provided, otherwise use child's class attribute
        child_access_policy = access_policy if access_policy is not None else child_endpoint.access_policy
        
        merged_access_policy = ConstraintMerger.merge_access_policies(
            parent=cls.access_policy,
            child=child_access_policy,
            replace_roles=cls.replace_roles,
            replace_scopes=cls.replace_scopes
        )
        
        # Step 7: Merge rate limits using ConstraintMerger
        # Use override if provided, otherwise use child's class attribute
        child_rate_limit = rate_limit if rate_limit is not None else child_endpoint.rate_limit
        
        merged_rate_limit = ConstraintMerger.merge_rate_limits(
            parent=cls.rate_limit,
            child=child_rate_limit
        )
        
        # Step 8: Build constraints object
        constraints = EndpointConstraints(
            access_policy=merged_access_policy,
            rate_limit=merged_rate_limit,
            scopes=merged_access_policy.scopes if merged_access_policy else [],
            roles=merged_access_policy.roles if merged_access_policy else []
        )
        
        # Step 9: Build extras dict from kwargs
        extras_dict: Dict[str, Any] = dict(kwargs)
        
        # Store serializers if child has them
        if child_endpoint.serializers:
            extras_dict["serializers"] = dict(child_endpoint.serializers)
        
        # Step 10: Create a placeholder handler for the child descriptor
        # The actual handler will be set when the child is decorated
        def placeholder_handler() -> None:
            pass
        
        placeholder_handler.__name__ = f"{child_endpoint.__name__}_child"
        placeholder_handler.__module__ = child_endpoint.__module__
        
        # Step 11: Create the descriptor
        descriptor = EndpointDescriptor(
            handler=placeholder_handler,
            module=child_endpoint.__module__,
            leaf=None,  # We use composed path instead
            path=composed_path,
            methods=child_methods,
            version=child_version,
            tags=merged_tags if merged_tags else [],
            constraints=constraints,
            doc=kwargs.get("doc"),
            extras=extras_dict
        )
        
        # Step 12: Register with EndpointRegistry
        EndpointRegistry.register(descriptor)
        
        return descriptor

    @classmethod
    def __init_subclass__(cls, **kwargs: Any) -> None:
        """
            Hook called when a subclass is created.

            This allows us to automatically fix the paths of endpoints
            that were decorated inside the class body, since decorators
            evaluate before the subclass is fully defined.
        """
        super().__init_subclass__(**kwargs)

        base = cls._get_base_path()
        if not base:
            return

        # Check all attributes defined in this subclass
        for name, attr in cls.__dict__.items():
            if callable(attr):
                # Look for matching descriptor in registry
                for desc in EndpointRegistry.collect():
                    if desc.handler is attr:
                        # Skip if absolute
                        if desc.extras.get("absolute", False):
                            continue

                        # Remove old index from registry
                        old_path = EndpointRegistry._get_index_path(desc)
                        for method in desc.methods:
                            EndpointRegistry._path_method_index.pop((old_path, method.upper()), None)

                        # Re-compose path using this class's base_path
                        new_path = cls._compose_path(leaf=desc.leaf, path=desc.path)
                        desc.path = new_path
                        desc.leaf = None

                        # Re-add to index
                        for method in desc.methods:
                            EndpointRegistry._path_method_index[(new_path, method.upper())] = desc
