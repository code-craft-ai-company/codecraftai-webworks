"""
.. module:: restblueprint
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: REST blueprint class for grouping related REST endpoints.

.. moduleauthor:: Code Craft AI LLC
"""

__author__ = "Code Craft AI LLC"
__copyright__ = "Copyright 2025, Code Craft AI LLC"
__credits__ = []

from typing import Any, Callable, Dict, List, Optional, Protocol, Type, TypeVar

from ccai.webworks.endpoints.accesspolicy import AccessPolicy
from ccai.webworks.endpoints.descriptor import EndpointDescriptor
from ccai.webworks.endpoints.doc import Doc
from ccai.webworks.endpoints.ratelimit import RateLimit
from ccai.webworks.endpoints.restendpoint import RestEndpoint


# Type variable for preserving function signatures in decorators
F = TypeVar("F", bound=Callable[..., Any])


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


class RestBlueprint(RestEndpoint):
    """
        Blueprint for REST API collections with shared versioning, tags,
        and authentication requirements.
        
        RestBlueprint extends RestEndpoint to represent a collection of REST
        nodes sharing higher-level metadata. It provides a register() hook
        that calls attach_at repeatedly to expose each child resource under
        the blueprint's parent path.
        
        Subclasses should define child endpoints by decorating methods with
        attach_at or by using the add_crud() helper to register standardized
        CRUD routes.
        
        Class Attributes:
            base_path: Base URL path for all child endpoints.
            base_leaf: Base URL leaf segment (alternative to base_path).
            replace_tags: If True, child tags replace parent tags instead of merging.
    """
    
    # Blueprint-specific attributes
    base_path: Optional[str] = None
    base_leaf: Optional[str] = None
    replace_tags: bool = False

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
            Merge child tags with blueprint tags according to replace_tags setting.
            
            :param child_tags: Tags specified for the child endpoint.
            
            :returns: Merged tags list, or None if no tags.
        """
        if cls.replace_tags:
            # replace_tags=True: child tags fully replace parent tags
            if child_tags is not None:
                return child_tags
            return None
        
        # Default behavior: merge (parent tags appended to child tags)
        result = list(child_tags) if child_tags else []
        
        for tag in cls.tags:
            if tag not in result:
                result.append(tag)
        
        return result if result else None
    
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
        absolute: bool = False,
        **extras
    ) -> Callable[[F], F]:
        """
            Decorator that binds a REST handler to a URL location relative to the blueprint's base.
            
            This method overrides RestEndpoint.attach_at to compute paths relative
            to the blueprint's base_path or base_leaf. It also handles tag
            merging and REST context inheritance.
            
            :param leaf: URL leaf segment (relative to blueprint base).
            :param path: Full URL path (relative to blueprint base unless absolute=True).
            :param methods: HTTP methods (defaults to class attribute).
            :param version: API version string (inherits from blueprint if not set).
            :param tags: Documentation tags (merged with blueprint tags by default).
            :param access_policy: Security policy (defaults to class attribute).
            :param rate_limit: Rate limiting config (defaults to class attribute).
            :param request_schema: Request body schema (dataclass or Pydantic).
            :param response_schema: Response body schema.
            :param error_map: Mapping of status codes to error schemas.
            :param doc: Documentation object with summary/description.
            :param on_conflict: "error" to raise on conflict, "replace" to override.
            :param absolute: If True, path overrides the blueprint prefix.
            :param extras: Additional kwargs stored in descriptor.extras.
            
            :returns: Decorator that returns the original function unchanged.
        """
        # Compute the full path relative to blueprint base (unless absolute)
        if absolute:
            computed_path = path
        else:
            computed_path = cls._compute_full_path(leaf, path)
        
        # Handle tag merging
        merged_tags = cls._merge_blueprint_tags(tags)
        
        # Inherit version from blueprint if not specified
        merged_version = version if version is not None else cls.version
        
        # Call parent attach_at with computed path
        # Mark as REST endpoint so the OpenAPI generator can distinguish
        # REST API routes from plain page routes. ``absolute`` is
        # also recorded so the inside-class-body re-resolution path
        # in :meth:`Endpoint.__init_subclass__` can short-circuit
        # for explicitly-absolute paths.
        extras["endpoint_type"] = "rest"
        extras["absolute"] = absolute

        inner_decorator = super().attach_at(
            leaf=None if computed_path else leaf,
            path=computed_path,
            methods=methods,
            version=merged_version,
            tags=merged_tags,
            access_policy=access_policy,
            rate_limit=rate_limit,
            request_schema=request_schema,
            response_schema=response_schema,
            error_map=error_map,
            doc=doc,
            on_conflict=on_conflict,
            **extras
        )

        # Stamp the inside-class-body metadata marker so
        # :meth:`Endpoint.__init_subclass__` can re-resolve the path
        # when this decoration was invoked against a parent class
        # (e.g. ``@RestBlueprint.attach_at(...)`` inside a subclass
        # body, where ``cls = RestBlueprint`` and ``base_path`` is
        # therefore ``None``). The marker captures the *original*
        # uncomposed ``leaf`` / ``path`` so the corrected path can
        # be computed against the subclass's base via
        # :meth:`_compose_path_for_attach`.
        return cls._wrap_inner_decorator_with_marker(
            inner_decorator=inner_decorator,
            leaf=leaf,
            path=path,
            absolute=absolute,
        )

    @classmethod
    def _compose_path_for_attach(
        cls,
        leaf: Optional[str],
        path: Optional[str],
        absolute: bool,
    ) -> Optional[str]:
        """
            Hook used by :meth:`Endpoint.__init_subclass__` to
            re-resolve the registered path of a method whose
            ``attach_at`` decorator was invoked against a parent
            class.

            Returns the path :class:`RestBlueprint` would have
            produced had the decoration been invoked against this
            subclass directly. ``absolute=True`` decorations
            short-circuit because their ``path`` was registered
            verbatim and should not be re-prefixed.

            :param leaf: Original leaf segment passed to
                         :meth:`attach_at`.
            :param path: Original path passed to :meth:`attach_at`.
            :param absolute: ``True`` when the caller passed
                             ``absolute=True``.

            :returns: Corrected path, or ``None`` to skip
                      re-resolution (the absolute case).
        """
        if absolute:
            return None

        rtnval = cls._compute_full_path(leaf=leaf, path=path)
        return rtnval

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
            
            Children inherit REST documentation context (tags, security schemes,
            version) from the blueprint without re-declaring them.
            
            :param router: Optional router to add endpoints to. If None,
                          descriptors are returned without router registration.
            
            :returns: List of EndpointDescriptor objects for all registered endpoints.
        """
        # Collect descriptors from the registry that belong to this blueprint
        all_descriptors = cls.marked_descriptors()
        
        # Filter to descriptors that were registered by this blueprint class
        blueprint_descriptors = cls._collect_blueprint_descriptors(all_descriptors)
        
        # If router is provided, add each descriptor to it
        if router is not None:
            for descriptor in blueprint_descriptors:
                router.add_endpoint(descriptor)
        
        return blueprint_descriptors
    
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
    def add_crud(
        cls,
        resource: str,
        schema: Type,
        list_handler: Optional[Callable] = None,
        create_handler: Optional[Callable] = None,
        read_handler: Optional[Callable] = None,
        update_handler: Optional[Callable] = None,
        delete_handler: Optional[Callable] = None
    ) -> List[EndpointDescriptor]:
        """
            Register standardized CRUD routes for a resource.
            
            This method registers up to five standard REST routes for a resource:
            - GET /{resource} - List all resources
            - POST /{resource} - Create a new resource
            - GET /{resource}/{id} - Read a single resource
            - PUT /{resource}/{id} - Update a resource
            - DELETE /{resource}/{id} - Delete a resource
            
            Documentation fields are auto-populated based on the resource name
            and schema.
            
            :param resource: Resource name (e.g., "users").
            :param schema: Pydantic/dataclass schema for the resource.
            :param list_handler: Handler for GET /resource (list).
            :param create_handler: Handler for POST /resource (create).
            :param read_handler: Handler for GET /resource/{id} (read).
            :param update_handler: Handler for PUT /resource/{id} (update).
            :param delete_handler: Handler for DELETE /resource/{id} (delete).
            
            :returns: List of EndpointDescriptor objects for registered routes.
        """
        descriptors: List[EndpointDescriptor] = []
        resource_title = resource.replace("_", " ").title()
        
        # GET /{resource} - List
        if list_handler is not None:
            doc = Doc(
                summary=f"List {resource_title}",
                description=f"Retrieve a list of all {resource_title.lower()} resources."
            )
            decorator = cls.read(
                leaf=resource,
                response_schema=schema,
                doc=doc
            )
            decorator(list_handler)
            # Get the descriptor that was just registered
            all_descs = cls.marked_descriptors()
            if all_descs:
                descriptors.append(all_descs[-1])
        
        # POST /{resource} - Create
        if create_handler is not None:
            doc = Doc(
                summary=f"Create {resource_title}",
                description=f"Create a new {resource_title.lower()} resource."
            )
            decorator = cls.create(
                leaf=resource,
                request_schema=schema,
                response_schema=schema,
                doc=doc
            )
            decorator(create_handler)
            all_descs = cls.marked_descriptors()
            if all_descs:
                descriptors.append(all_descs[-1])
        
        # GET /{resource}/{id} - Read
        if read_handler is not None:
            doc = Doc(
                summary=f"Get {resource_title}",
                description=f"Retrieve a single {resource_title.lower()} resource by ID."
            )
            decorator = cls.read(
                path=f"{resource}/{{id}}",
                response_schema=schema,
                doc=doc
            )
            decorator(read_handler)
            all_descs = cls.marked_descriptors()
            if all_descs:
                descriptors.append(all_descs[-1])
        
        # PUT /{resource}/{id} - Update
        if update_handler is not None:
            doc = Doc(
                summary=f"Update {resource_title}",
                description=f"Update an existing {resource_title.lower()} resource."
            )
            decorator = cls.update(
                path=f"{resource}/{{id}}",
                request_schema=schema,
                response_schema=schema,
                doc=doc
            )
            decorator(update_handler)
            all_descs = cls.marked_descriptors()
            if all_descs:
                descriptors.append(all_descs[-1])
        
        # DELETE /{resource}/{id} - Delete
        if delete_handler is not None:
            doc = Doc(
                summary=f"Delete {resource_title}",
                description=f"Delete a {resource_title.lower()} resource."
            )
            decorator = cls.delete(
                path=f"{resource}/{{id}}",
                doc=doc
            )
            decorator(delete_handler)
            all_descs = cls.marked_descriptors()
            if all_descs:
                descriptors.append(all_descs[-1])
        
        return descriptors
