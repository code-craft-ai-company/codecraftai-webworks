"""
.. module:: endpoint
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: Base endpoint class for declarative HTTP endpoint definition.

.. moduleauthor:: Code Craft AI LLC
"""

__author__ = "Code Craft AI LLC"
__copyright__ = "Copyright 2025, Code Craft AI LLC"
__credits__ = []

import dataclasses
from typing import Any, Callable, Dict, List, Optional, Type, TypeVar

from ccai.webworks.endpoints.accesspolicy import AccessPolicy
from ccai.webworks.endpoints.constraints import EndpointConstraints
from ccai.webworks.endpoints.descriptor import (
    ENDPOINT_DECLARED_ATTR,
    ENDPOINT_DESCRIPTORS_ATTR,
    declare_on_class,
    EndpointDescriptor,
    mark_handler
)
from ccai.webworks.endpoints.doc import Doc
from ccai.webworks.endpoints.exceptions import EndpointRegistrationError
from ccai.webworks.endpoints.ratelimit import RateLimit
from ccai.webworks.security.decorators import HANDLER_POLICY_ATTR


# Type variable for preserving function signatures in decorators
F = TypeVar("F", bound=Callable[..., Any])



class Endpoint:
    """
        Base class providing a reusable container for endpoint constraints
        and metadata. Supports both direct attachment via attach_at() and
        hierarchical composition via attach_child().
        
        Subclasses can override class-level attributes to define default
        constraints that apply to all handlers decorated with attach_at().
        Explicit kwargs passed to attach_at() override class attributes.
        
        Class Attributes:
            access_policy: Default access policy for all handlers.
            rate_limit: Default rate limit for all handlers.
            methods: Default HTTP methods (defaults to ["GET"]).
            version: Default API version string.
            tags: Default documentation tags.
            serializers: Default serializer configuration.
    """
    
    # Class-level defaults that subclasses can override
    access_policy: Optional[AccessPolicy] = None
    rate_limit: Optional[RateLimit] = None
    methods: List[str] = ["GET"]
    version: Optional[str] = None
    tags: List[str] = []
    serializers: Dict[str, Any] = {}

    # Blueprint-related attributes (used by attach_child)
    base_path: Optional[str] = None
    base_leaf: Optional[str] = None

    # Function-attribute name used to record the original
    # ``leaf`` / ``path`` / ``absolute`` arguments passed to
    # :meth:`attach_at`, plus the class on which the decorator was
    # *invoked*. Read by :meth:`__init_subclass__` to detect the
    # inside-class-body decoration pattern (decorator invoked against
    # a parent class because the subclass isn't yet defined at
    # decorator-evaluation time) and re-resolve the registered
    # descriptor's path against the actual subclass's base.
    _ATTACH_AT_METADATA_ATTR: str = "_endpoint_attach_at_metadata"

    def __init_subclass__(cls, **kwargs: Any) -> None:
        """
            Repair endpoint paths for methods whose ``attach_at``
            decorator was invoked against a *parent* class.

            Decorator expressions inside a class body run *before*
            the enclosing class is fully defined, so a method
            written as::

                class MyBP(RestBlueprint):
                    base_path = "/inner"

                    @RestBlueprint.attach_at(leaf="thing", methods=["GET"])
                    def thing(self, request): ...

            invokes ``attach_at`` with ``cls = RestBlueprint`` rather
            than ``cls = MyBP``. The descriptor that lands in the
            registry therefore carries ``RestBlueprint``'s
            (``None``-valued) ``base_path``, producing ``/thing``
            when the user clearly meant ``/inner/thing``.

            This hook walks ``cls.__dict__`` (only methods defined
            *directly* on this subclass — inherited methods were
            fixed when their owning class was first created), looks
            for the metadata marker
            :data:`_ATTACH_AT_METADATA_ATTR` that
            :meth:`attach_at` stashes on each decorated function, and
            when the marker says decoration happened on a strict
            ancestor of ``cls`` re-resolves the path via
            :meth:`_compose_path_for_attach` and patches the
            descriptor in place via
            :meth:`EndpointRegistry.update_descriptor_path`.

            Methods decorated with ``absolute=True`` are intentionally
            outside any blueprint base prefix; subclasses can return
            the original path from
            :meth:`_compose_path_for_attach` to skip re-resolution.

            The walk is bounded by ``len(cls.__dict__)``, so the cost
            is O(methods on this subclass) regardless of how many
            other endpoints exist in the registry.

            :param kwargs: Forwarded to :class:`type.__init_subclass__`.
        """
        super().__init_subclass__(**kwargs)

        marker_attr = cls._ATTACH_AT_METADATA_ATTR

        for attr_value in list(cls.__dict__.values()):
            # Unwrap ``classmethod`` / ``staticmethod`` wrappers so
            # the marker check sees the underlying function.
            handler = attr_value
            if isinstance(handler, (classmethod, staticmethod)):
                handler = handler.__func__

            if not callable(handler):
                continue

            metadata = getattr(handler, marker_attr, None)
            if metadata is None:
                continue

            owner = metadata.get("owner")
            if owner is None or owner is cls:
                # Decoration happened on this exact class. The path
                # was already composed against the right base.
                continue

            if not issubclass(cls, owner):
                # Decoration wasn't from an ancestor — leave it
                # alone. (This branch shouldn't fire in practice;
                # the marker is only set by ``attach_at`` on
                # ``cls`` or its ancestors.)
                continue

            corrected_path = cls._compose_path_for_attach(
                leaf=metadata.get("leaf"),
                path=metadata.get("path"),
                absolute=bool(metadata.get("absolute")),
            )
            if corrected_path is None:
                continue

            descriptors = cls._find_descriptors_for_handler(handler)
            if len(descriptors) == 0:
                continue

            for descriptor in descriptors:
                # The descriptor is still only a mark on the handler at this
                # point -- no registry has collected it yet -- so correcting
                # the path is a plain assignment. Previously this had to
                # reach into the global registry and move index entries,
                # because registration had already happened at decoration.
                descriptor.path = corrected_path

            # Anchor the marker to the resolved subclass so deeper
            # subclasses that don't override this method won't try
            # to re-resolve it. (They wouldn't anyway — the walk
            # only inspects ``cls.__dict__`` — but explicit is
            # better.)
            metadata["owner"] = cls

        return

    @classmethod
    def _compose_path_for_attach(
        cls,
        leaf: Optional[str],
        path: Optional[str],
        absolute: bool,
    ) -> Optional[str]:
        """
            Hook called by :meth:`__init_subclass__` to compute the
            corrected path for a parent-class-decorated method.

            The default implementation returns ``None``, signalling
            "no path correction" — appropriate for plain
            :class:`Endpoint` subclasses that don't have a base path.
            Subclass families with a base path (:class:`Blueprint`,
            :class:`RestBlueprint`) override this hook to delegate to
            their respective composition methods.

            :param leaf: Original leaf passed to :meth:`attach_at`.
            :param path: Original path passed to :meth:`attach_at`.
            :param absolute: ``True`` when the caller declared the
                             path absolute (no base composition).

            :returns: Corrected path, or ``None`` to skip
                      re-resolution.
        """
        return None

    @classmethod
    def _wrap_inner_decorator_with_marker(
        cls,
        inner_decorator: Callable[[F], F],
        leaf: Optional[str],
        path: Optional[str],
        absolute: bool,
    ) -> Callable[[F], F]:
        """
            Wrap an :meth:`attach_at` inner decorator so the function
            it returns carries the metadata marker that
            :meth:`__init_subclass__` reads.

            Used by subclasses (:class:`Blueprint`,
            :class:`RestBlueprint`) that compose paths against a
            ``base_path``. The marker captures the *original*
            uncomposed ``leaf`` / ``path`` so the post-class-creation
            walk can re-resolve the path when decoration happened
            against an ancestor.

            Stacked decorators on the same function leave only the
            first marker. That covers the common case (multiple
            methods on a single handler with the same leaf / path).
            Stacked decorators with *different* leaves or paths
            against a parent class are not all re-resolved correctly
            — a deliberate scope limitation.

            :param inner_decorator: Decorator returned by the
                                    superclass ``attach_at`` that
                                    actually registers the descriptor.
            :param leaf: Original leaf passed to the outer ``attach_at``.
            :param path: Original path passed to the outer ``attach_at``.
            :param absolute: ``True`` when the caller declared the
                             path absolute.

            :returns: A decorator that runs the inner decorator and
                      stamps the metadata marker on the resulting
                      function.
        """
        marker_attr = cls._ATTACH_AT_METADATA_ATTR
        owner_class = cls

        def stamping_decorator(func: F) -> F:
            decorated = inner_decorator(func)

            if not hasattr(decorated, marker_attr):
                setattr(
                    decorated,
                    marker_attr,
                    {
                        "owner": owner_class,
                        "leaf": leaf,
                        "path": path,
                        "absolute": absolute,
                    },
                )

            return decorated

        return stamping_decorator

    @classmethod
    def _find_descriptors_for_handler(
        cls,
        handler: Callable[..., Any],
    ) -> List[EndpointDescriptor]:
        """
            Locate every registered descriptor produced by
            :meth:`attach_at` invocations against *handler*.

            The registry is keyed by ``(path, method)`` rather than
            by handler identity, so we scan linearly. Cardinality is
            small (one or two descriptors per handler — stacked
            decorators with multiple methods on the same handler);
            the scan runs once per handler at class-definition time,
            never on the request path.

            :param handler: Callable that was passed through
                            :meth:`attach_at`.

            :returns: List of matching descriptors. Empty when the
                      handler is not registered.
        """
        marks = getattr(handler, ENDPOINT_DESCRIPTORS_ATTR, None)
        if marks is None:
            return []

        rtnval: List[EndpointDescriptor] = list(marks)

        return rtnval

    @classmethod
    def marked_descriptors(cls) -> List[EndpointDescriptor]:
        """
            Every descriptor declared by a handler on this class or an
            ancestor of it.

            Callers used to reach for ``EndpointRegistry.collect()`` and then
            filter the whole process's endpoints down to the ones belonging
            to a class. The descriptors now live on the handlers themselves,
            so a class can be asked directly and the answer does not depend
            on what else has been imported.

            Two sources are combined. Handlers written in a class body are
            found by walking the MRO, so a subclass inherits its bases'
            endpoints. Handlers attached as free functions -- the ordinary
            way to write a blueprint -- are not members of any class, so
            those come from the list ``attach_at`` left on this class, and
            that list is read from ``cls.__dict__`` only. See
            :data:`~ccai.webworks.endpoints.descriptor.ENDPOINT_DECLARED_ATTR`
            for why inheriting it would recreate the global registry.

            Declared descriptors come last and stay in declaration order:
            :meth:`RestBlueprint.add_crud` attaches a handler and then takes
            the final entry as the one it just made.

            :returns: Descriptors in method-resolution order, nearest class
                      first, with duplicates from inherited handlers removed.
        """
        rtnval: List[EndpointDescriptor] = []
        seen: List[int] = []

        for klass in cls.__mro__:
            for value in list(vars(klass).values()):
                handler = value
                if isinstance(handler, (classmethod, staticmethod)):
                    handler = handler.__func__
                if not callable(handler):
                    continue
                for descriptor in getattr(handler, ENDPOINT_DESCRIPTORS_ATTR, ()):
                    if id(descriptor) in seen:
                        continue
                    seen.append(id(descriptor))
                    rtnval.append(descriptor)

        for descriptor in cls.__dict__.get(ENDPOINT_DECLARED_ATTR, ()):
            if id(descriptor) in seen:
                continue
            seen.append(id(descriptor))
            rtnval.append(descriptor)

        return rtnval

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
            Decorator that binds a handler to an absolute URL location.
            
            This classmethod returns a decorator that registers the handler
            with the EndpointRegistry. The decorator returns the original
            function unchanged, allowing decorator stacking to work correctly.
            
            Class attributes are used as defaults for any parameters not
            explicitly provided. Explicit kwargs override class attributes.
            
            :param leaf: URL leaf segment (e.g., "status" -> /status).
            :param path: Full URL path (alternative to leaf).
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
        def decorator(func: F) -> F:
            # Validate mandatory metadata
            if leaf is None and path is None:
                raise EndpointRegistrationError(
                    message="Either 'leaf' or 'path' must be provided to attach_at()",
                    endpoint=cls,
                    missing_fields=["leaf", "path"]
                )
            
            # Merge class attributes with kwargs (kwargs override)
            merged_methods = methods if methods is not None else list(cls.methods)
            merged_version = version if version is not None else cls.version
            merged_tags = tags if tags is not None else list(cls.tags)
            merged_access_policy = access_policy if access_policy is not None else cls.access_policy
            merged_rate_limit = rate_limit if rate_limit is not None else cls.rate_limit

            # Honor any AccessPolicy attached to the handler by security
            # decorators (require_auth, require_roles, require_scopes,
            # public_endpoint). The decorator's policy is merged into the
            # one already resolved from explicit kwargs / class attributes
            # so decorator-supplied roles and scopes accumulate via
            # AccessPolicy.merge_with rather than being silently dropped.
            handler_policy = getattr(func, HANDLER_POLICY_ATTR, None)
            if handler_policy is not None:
                if merged_access_policy is None:
                    merged_access_policy = handler_policy
                else:
                    merged_access_policy = merged_access_policy.merge_with(handler_policy)

            # Build constraints object
            constraints = EndpointConstraints(
                access_policy=merged_access_policy,
                rate_limit=merged_rate_limit,
                scopes=merged_access_policy.scopes if merged_access_policy else [],
                roles=merged_access_policy.roles if merged_access_policy else []
            )
            
            # Build extras dict with any additional kwargs
            extras_dict: Dict[str, Any] = dict(extras)
            
            # Add REST-specific extras if provided
            if request_schema is not None or response_schema is not None or error_map is not None:
                rest_extras: Dict[str, Any] = {}
                if request_schema is not None:
                    rest_extras["request_schema"] = cls._inspect_schema(request_schema)
                if response_schema is not None:
                    rest_extras["response_schema"] = cls._inspect_schema(response_schema)
                if error_map is not None:
                    rest_extras["error_map"] = {
                        code: cls._inspect_schema(schema)
                        for code, schema in error_map.items()
                    }
                extras_dict["rest"] = rest_extras
            
            # Store serializers in extras if class has them
            if cls.serializers:
                extras_dict["serializers"] = dict(cls.serializers)
            
            # Create the descriptor
            descriptor = EndpointDescriptor(
                handler=func,
                module=func.__module__,
                leaf=leaf,
                path=path,
                methods=merged_methods,
                version=merged_version,
                tags=merged_tags,
                constraints=constraints,
                doc=doc,
                extras=extras_dict
            )
            
            # Mark the function with its descriptor. Registration is a
            # separate, explicit step -- an application builds an
            # EndpointRegistry and calls collect_from(...) on the modules it
            # wants. Importing a module of handlers has no global effect.
            #
            # The mark is read out of func.__dict__ rather than with getattr
            # so that a method defined on a subclass does not append to a
            # list that belongs to its base class.
            descriptor.on_conflict = on_conflict
            mark_handler(func, descriptor)

            # Also record it against the class it was declared through, so
            # `cls.register()` can find handlers that are free functions
            # rather than members of the class body.
            declare_on_class(cls, descriptor)

            # Return the original function unchanged
            return func
        
        return decorator

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
        replace_scopes: bool = False,
        replace_roles: bool = False,
        merge_tags: bool = False,
        **kwargs
    ) -> EndpointDescriptor:
        """
            Attach a child endpoint relative to this endpoint's base path.
            
            This method creates a descriptor for the child endpoint with
            paths computed relative to the parent's base_path/base_leaf.
            Constraints are merged following inheritance rules.
            
            :param child_endpoint: The child endpoint class to attach.
            :param leaf: Override for child's leaf (relative to parent base).
            :param path: Override for child's path (relative to parent base).
            :param methods: Override for child's methods.
            :param version: Override for child's version.
            :param tags: Override for child's tags.
            :param access_policy: Override for child's access policy.
            :param rate_limit: Override for child's rate limit.
            :param replace_scopes: If True, child scopes replace parent scopes.
            :param replace_roles: If True, child roles replace parent roles.
            :param merge_tags: If True, parent tags are appended to child tags.
            :param kwargs: Additional overrides for child descriptor.
            
            :returns: The merged EndpointDescriptor for the child.
        """
        # Determine child's leaf/path
        child_leaf = leaf if leaf is not None else child_endpoint.base_leaf
        child_path = path if path is not None else child_endpoint.base_path
        
        # Compute the final path relative to parent's base
        final_path = cls._compute_child_path(child_leaf, child_path)
        
        # Determine final leaf (None if we computed a full path)
        final_leaf = None
        if final_path is None:
            # No path computed, use leaf directly
            final_leaf = child_leaf
        
        # Merge methods
        merged_methods = methods if methods is not None else list(child_endpoint.methods)
        
        # Merge version (child overrides parent)
        merged_version = version if version is not None else child_endpoint.version
        if merged_version is None:
            merged_version = cls.version
        
        # Merge tags
        child_tags = tags if tags is not None else list(child_endpoint.tags)
        if merge_tags:
            # Parent tags appended to child tags
            merged_tags = list(child_tags)
            for tag in cls.tags:
                if tag not in merged_tags:
                    merged_tags.append(tag)
        else:
            # Child tags win (default behavior)
            merged_tags = child_tags if child_tags else list(cls.tags)
        
        # Build parent constraints
        parent_constraints = EndpointConstraints(
            access_policy=cls.access_policy,
            rate_limit=cls.rate_limit,
            scopes=cls.access_policy.scopes if cls.access_policy else [],
            roles=cls.access_policy.roles if cls.access_policy else []
        )
        
        # Build child constraints
        child_access_policy = access_policy if access_policy is not None else child_endpoint.access_policy
        child_rate_limit = rate_limit if rate_limit is not None else child_endpoint.rate_limit
        child_constraints = EndpointConstraints(
            access_policy=child_access_policy,
            rate_limit=child_rate_limit,
            scopes=child_access_policy.scopes if child_access_policy else [],
            roles=child_access_policy.roles if child_access_policy else []
        )
        
        # Merge constraints following inheritance rules
        merged_constraints = EndpointConstraints.merge(
            parent_constraints,
            child_constraints,
            replace_scopes=replace_scopes,
            replace_roles=replace_roles
        )
        
        # Build extras from kwargs
        extras_dict: Dict[str, Any] = dict(kwargs)
        
        # Store serializers if child has them
        if child_endpoint.serializers:
            extras_dict["serializers"] = dict(child_endpoint.serializers)
        
        # Create a placeholder handler for the child descriptor
        # The actual handler will be set when the child is decorated
        def placeholder_handler() -> None:
            pass
        
        placeholder_handler.__name__ = f"{child_endpoint.__name__}_child"
        placeholder_handler.__module__ = child_endpoint.__module__
        
        # Create the descriptor
        descriptor = EndpointDescriptor(
            handler=placeholder_handler,
            module=child_endpoint.__module__,
            leaf=final_leaf,
            path=final_path,
            methods=merged_methods,
            version=merged_version,
            tags=merged_tags,
            constraints=merged_constraints,
            doc=kwargs.get("doc"),
            extras=extras_dict
        )
        
        return descriptor
    
    @classmethod
    def _compute_child_path(
        cls,
        child_leaf: Optional[str],
        child_path: Optional[str]
    ) -> Optional[str]:
        """
            Compute the final path for a child endpoint.
            
            The child's path is computed relative to the parent's
            base_path or base_leaf.
            
            :param child_leaf: The child's leaf segment.
            :param child_path: The child's path.
            
            :returns: The computed path, or None if no path can be computed.
        """
        # Determine parent base
        parent_base = cls.base_path
        if parent_base is None and cls.base_leaf is not None:
            parent_base = f"/{cls.base_leaf}"
        
        if parent_base is None:
            # No parent base, return child path as-is
            if child_path is not None:
                return child_path
            return None
        
        # Ensure parent base doesn't end with /
        parent_base = parent_base.rstrip("/")
        
        # Compute child path relative to parent
        if child_path is not None:
            # Child has explicit path
            if child_path.startswith("/"):
                # Absolute path - append to parent base
                return f"{parent_base}{child_path}"
            else:
                # Relative path
                return f"{parent_base}/{child_path}"
        elif child_leaf is not None:
            # Child has leaf - append to parent base
            return f"{parent_base}/{child_leaf}"
        else:
            # No child path or leaf - use parent base
            return parent_base
    
    @classmethod
    def _inspect_schema(cls, schema: Type) -> Dict[str, Any]:
        """
            Inspect a schema type and extract JSON schema information.
            
            Supports Pydantic models (via model_json_schema) and
            dataclasses (via __dataclass_fields__).
            
            :param schema: The schema type to inspect.
            
            :returns: Dictionary containing JSON schema information.
        """
        # Try Pydantic model first
        if hasattr(schema, "model_json_schema"):
            return schema.model_json_schema()
        
        # Try dataclass
        if hasattr(schema, "__dataclass_fields__"):
            return cls._dataclass_to_schema(schema)
        
        # Return a reference schema for unknown types
        return {"$ref": f"#/components/schemas/{schema.__name__}"}
    
    @classmethod
    def _dataclass_to_schema(cls, schema: Type) -> Dict[str, Any]:
        """
            Convert a dataclass to a JSON schema representation.
            
            :param schema: The dataclass type to convert.
            
            :returns: Dictionary containing JSON schema information.
        """
        properties: Dict[str, Any] = {}
        required: List[str] = []
        
        for field_name, field_info in schema.__dataclass_fields__.items():
            field_type = field_info.type
            properties[field_name] = cls._type_to_schema(field_type)
            
            # Check if field has a default — a field is required when
            # both .default and .default_factory are the MISSING sentinel.
            if (field_info.default is dataclasses.MISSING
                    and field_info.default_factory is dataclasses.MISSING):
                required.append(field_name)
        
        result: Dict[str, Any] = {
            "type": "object",
            "properties": properties,
        }
        
        if required:
            result["required"] = required
        
        return result
    
    @classmethod
    def _type_to_schema(cls, field_type: Any) -> Dict[str, Any]:
        """
            Convert a Python type to a JSON schema type.
            
            :param field_type: The Python type to convert.
            
            :returns: Dictionary containing JSON schema type information.
        """
        # Handle basic types
        type_mapping = {
            str: {"type": "string"},
            int: {"type": "integer"},
            float: {"type": "number"},
            bool: {"type": "boolean"},
            list: {"type": "array"},
            dict: {"type": "object"},
        }
        
        if field_type in type_mapping:
            return type_mapping[field_type]
        
        # Handle string type annotations
        if isinstance(field_type, str):
            return {"type": "string"}
        
        # Default to string for unknown types
        return {"type": "string"}
