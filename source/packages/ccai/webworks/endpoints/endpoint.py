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
import inspect
import os

from typing import Any, Callable, Dict, List, Optional, Tuple, Type, TypeVar

from ccai.webworks.endpoints.accesspolicy import AccessPolicy
from ccai.webworks.endpoints.constraints import EndpointConstraints
from ccai.webworks.endpoints.descriptor import (
    ENDPOINT_DECLARED_ATTR,
    ENDPOINT_DESCRIPTORS_ATTR,
    ENDPOINT_PARENT_PLACEMENT_EXTRA,
    REST_ERROR_MAP_TYPES_EXTRA,
    REST_REQUEST_SCHEMA_TYPE_EXTRA,
    REST_RESPONSE_SCHEMA_TYPE_EXTRA,
    declare_on_class,
    EndpointDescriptor,
    mark_handler,
    record_rest_processing
)
from ccai.webworks.endpoints.doc import Doc
from ccai.webworks.endpoints.exceptions import EndpointRegistrationError
from ccai.webworks.endpoints.merging import ConstraintMerger
from ccai.webworks.endpoints.ratelimit import RateLimit
from ccai.webworks.endpoints.typeinspection import dataclass_to_json_schema, type_to_json_schema
from ccai.webworks.security.decorators import HANDLER_POLICY_ATTR


# Type variable for preserving function signatures in decorators
F = TypeVar("F", bound=Callable[..., Any])


#: Attribute set on the stand-in handler of a placement descriptor -- the
#: descriptor ``attach_child`` returns to say *where* a child was placed. A
#: placement is not a route: the child's own handlers are re-placed under it
#: and those are what a router serves.
UNROUTED_PLACEMENT_ATTR = "__webworks_unrouted_placement__"

#: Attribute, stored in a class's own ``__dict__``, caching the descriptors
#: whose class-body handlers were bound for that class. Keyed by the id of
#: the declared descriptor so repeated ``register()`` calls return the same
#: objects.
BOUND_DESCRIPTORS_ATTR = "__webworks_bound_descriptors__"

#: Attribute, stored in a class's own ``__dict__``, holding the instance
#: that class-body handlers taking ``self`` are bound to.
HANDLER_INSTANCE_ATTR = "__webworks_handler_instance__"



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
            rest_processing: Default for ``attach_at(rest_processing=...)``:
                whether a handler declared with REST metadata (a request
                schema, a response schema or an error map) is served
                through the REST request/response processing. True; the
                authentication blueprints set it to False because their
                handlers parse the body and shape the response themselves.
    """
    
    # Class-level defaults that subclasses can override
    access_policy: Optional[AccessPolicy] = None
    rate_limit: Optional[RateLimit] = None
    methods: List[str] = ["GET"]
    version: Optional[str] = None
    tags: List[str] = []
    serializers: Dict[str, Any] = {}
    rest_processing: bool = True

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

            descriptors = cls._find_descriptors_for_handler(handler)
            if len(descriptors) == 0:
                continue

            # The decorator ran against the ancestor, so the descriptor
            # carries the ancestor's access policy and rate limit, not
            # this subclass's. Merge this class's in now; otherwise a
            # blueprint that declares ``access_policy`` and writes its
            # handlers in its own body would serve them unprotected.
            cls._apply_class_constraints(descriptors)

            # A blueprint claims the routes written in its body.
            cls._claim_ancestor_descriptors(descriptors, owner)

            corrected_path = cls._compose_path_for_attach(
                leaf=metadata.get("leaf"),
                path=metadata.get("path"),
                absolute=bool(metadata.get("absolute")),
            )

            if corrected_path is not None:
                for descriptor in descriptors:
                    # The descriptor is still only a mark on the handler at
                    # this point -- no registry has collected it yet -- so
                    # correcting the path is a plain assignment. Previously
                    # this had to reach into the global registry and move
                    # index entries, because registration had already
                    # happened at decoration.
                    descriptor.path = corrected_path

            # Anchor the marker to the resolved subclass so deeper
            # subclasses that don't override this method won't try
            # to re-resolve it. (They wouldn't anyway — the walk
            # only inspects ``cls.__dict__`` — but explicit is
            # better.)
            metadata["owner"] = cls

        return

    @classmethod
    def _claim_ancestor_descriptors(cls, descriptors: List[EndpointDescriptor], owner: type) -> None:
        """
            Hook for subclasses: take ownership of descriptors that a
            handler in this class's body declared through an ancestor's
            ``attach_at``. A plain endpoint records nothing; a blueprint
            records its name (see :class:`Blueprint`).

            :param descriptors: The descriptors to update in place.
            :param owner: The ancestor class ``attach_at`` ran against.
        """
        return

    @classmethod
    def _apply_class_constraints(cls, descriptors: List[EndpointDescriptor]) -> None:
        """
            Merge this class's access policy and rate limit into descriptors
            that were declared through an ancestor.

            Merging follows the blueprint composition rules: roles and scopes
            accumulate (unless the class sets ``replace_roles`` or
            ``replace_scopes``) and the most restrictive rate limit wins, so
            the result is never weaker than what the class declares.

            :param descriptors: The descriptors to update in place.
        """
        if cls.access_policy is None and cls.rate_limit is None:
            return

        for descriptor in descriptors:
            merged_policy = ConstraintMerger.merge_access_policies(
                parent=cls.access_policy,
                child=descriptor.constraints.access_policy,
                replace_roles=bool(getattr(cls, "replace_roles", False)),
                replace_scopes=bool(getattr(cls, "replace_scopes", False))
            )
            merged_rate_limit = ConstraintMerger.merge_rate_limits(
                parent=cls.rate_limit,
                child=descriptor.constraints.rate_limit
            )
            descriptor.constraints = EndpointConstraints(
                access_policy=merged_policy,
                rate_limit=merged_rate_limit,
                scopes=merged_policy.scopes if merged_policy else [],
                roles=merged_policy.roles if merged_policy else []
            )

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
    def routable_descriptors(cls, include_declared: bool = True) -> List[EndpointDescriptor]:
        """
            The descriptors of this class in the form a router can serve.

            This is :meth:`marked_descriptors` with one difference. A handler
            written in a class body is stored on its descriptor as the plain
            function, so a method declared ``def thing(self, request)`` would
            be called with the request in the ``self`` position. Here such a
            handler is bound first -- a method taking ``self`` to an instance
            of the class it is written in, a ``classmethod`` to that class --
            and the descriptor returned for it is a copy carrying the bound
            handler. The declared descriptor, which is the mark on the
            function, is left untouched.

            A handler inherited from a base class is bound to the base class
            that defines it, not to this subclass. Its route was resolved
            against that base class's path and is one route however many
            subclasses inherit it, so every subclass returns the same
            descriptor object for it and a registry given both the base and
            a subclass registers the route once.

            Static methods, and class-body functions that do not take
            ``self``, are returned as declared.

            :param include_declared: Include the free functions declared
                through this class (``cls.attach_at(...)`` at module level).
                A registry walking the classes of a module passes False,
                because those functions are members of their own module and
                are collected from there.

            :returns: Descriptors ready for a router, in the order of
                      :meth:`marked_descriptors`.

            :raises EndpointRegistrationError: If a handler takes ``self``
                and the class that defines it cannot be instantiated without
                arguments.
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
                    binder = cls
                    if isinstance(klass, type) and issubclass(klass, Endpoint):
                        binder = klass
                    rtnval.append(binder._bind_class_body_descriptor(descriptor, value))

        if include_declared:
            for descriptor in cls.__dict__.get(ENDPOINT_DECLARED_ATTR, ()):
                if id(descriptor) in seen:
                    continue
                seen.append(id(descriptor))
                rtnval.append(descriptor)

        return rtnval

    @classmethod
    def _bind_class_body_descriptor(cls, descriptor: EndpointDescriptor, member: Any) -> EndpointDescriptor:
        """
            Give a descriptor declared in a class body a handler the
            dispatcher can call with just the request.

            :param descriptor: The descriptor as declared.
            :param member: The class attribute the handler was found as: the
                           function itself, or its ``classmethod`` /
                           ``staticmethod`` wrapper.

            :returns: ``descriptor`` when its handler needs no binding,
                      otherwise a copy of it holding the bound handler.
        """
        if isinstance(member, staticmethod):
            return descriptor

        if descriptor.handler is not getattr(member, "__func__", member):
            # The descriptor does not hold the function this attribute
            # wraps (a placement, or one already bound); leave it alone.
            return descriptor

        binds_to_class = isinstance(member, classmethod)
        if not binds_to_class and not cls._handler_takes_self(descriptor.handler):
            return descriptor

        cache: Optional[Dict[int, Tuple[EndpointDescriptor, EndpointDescriptor]]]
        cache = cls.__dict__.get(BOUND_DESCRIPTORS_ATTR)
        if cache is None:
            cache = {}
            setattr(cls, BOUND_DESCRIPTORS_ATTR, cache)

        cached = cache.get(id(descriptor))
        if cached is not None and cached[0] is descriptor:
            bound_descriptor = cached[1]
            # The declared descriptor is the source of truth for everything
            # but the handler; carry over a path corrected since the copy.
            bound_descriptor.path = descriptor.path
            bound_descriptor.leaf = descriptor.leaf
            return bound_descriptor

        if binds_to_class:
            bound_handler = descriptor.handler.__get__(cls, cls)
        else:
            bound_handler = descriptor.handler.__get__(cls._handler_instance(), cls)

        bound_descriptor = dataclasses.replace(descriptor, handler=bound_handler)
        cache[id(descriptor)] = (descriptor, bound_descriptor)

        return bound_descriptor

    @staticmethod
    def _handler_takes_self(handler: Callable[..., Any]) -> bool:
        """
            Whether a class-body function is an instance method, judged the
            way Python programmers judge it: its first parameter is ``self``.

            :param handler: The function found in a class body.

            :returns: True when the first positional parameter is named
                      ``self``.
        """
        try:
            parameters = list(inspect.signature(handler).parameters.values())
        except (TypeError, ValueError):
            return False

        if len(parameters) == 0:
            return False

        rtnval = parameters[0].name == "self"
        return rtnval

    @classmethod
    def _handler_instance(cls) -> Any:
        """
            The instance of this class that handlers taking ``self`` are
            bound to. Created on first use and kept, so every handler of the
            class shares one instance.

            :returns: An instance of this class.

            :raises EndpointRegistrationError: If the class cannot be
                instantiated without arguments.
        """
        instance = cls.__dict__.get(HANDLER_INSTANCE_ATTR)
        if instance is not None:
            return instance

        try:
            instance = cls()
        except TypeError as exc:
            errmsg_lines = [
                f"Cannot bind the instance-method handlers of '{cls.__name__}':",
                f"the class cannot be instantiated without arguments ({exc}).",
                "Give the class a no-argument constructor, or declare the handlers "
                "with @staticmethod so they do not take 'self'.",
            ]
            errmsg = os.linesep.join(errmsg_lines)
            raise EndpointRegistrationError(
                message=errmsg,
                endpoint=cls,
                missing_fields=[]
            ) from exc

        setattr(cls, HANDLER_INSTANCE_ATTR, instance)

        return instance

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
        rest_processing: Optional[bool] = None,
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
            :param rest_processing: Whether a handler declared with REST
                metadata (``request_schema``, ``response_schema`` or
                ``error_map``) is served through the REST request/response
                processing when a web application serves it: content
                negotiation (406/415), body validation (400, the payload is
                read with ``get_rest_payload(request)``), serialization of
                the result and the ``RESTError`` error body. Pass False for
                a handler that parses the body and shapes the response
                itself; its schemas then only document it. None takes the
                class attribute :attr:`rest_processing` (True).
            :param extras: Additional kwargs stored in descriptor.extras.
            
            :returns: Decorator that returns the original function unchanged.
            
            :raises EndpointRegistrationError: If mandatory metadata missing.
            :raises EndpointConflictError: If path+method conflicts with existing.
        """
        merged_rest_processing = rest_processing if rest_processing is not None else cls.rest_processing

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
                # The inspected JSON-schema dict is what documentation
                # exports read. The schema class itself is kept beside it:
                # validating a request body and generating an OpenAPI
                # component both need the class, which cannot be recovered
                # from the dict.
                rest_extras: Dict[str, Any] = {}
                if request_schema is not None:
                    rest_extras["request_schema"] = cls._inspect_schema(request_schema)
                    rest_extras[REST_REQUEST_SCHEMA_TYPE_EXTRA] = request_schema
                if response_schema is not None:
                    rest_extras["response_schema"] = cls._inspect_schema(response_schema)
                    rest_extras[REST_RESPONSE_SCHEMA_TYPE_EXTRA] = response_schema
                if error_map is not None:
                    rest_extras["error_map"] = {
                        code: cls._inspect_schema(schema)
                        for code, schema in error_map.items()
                    }
                    rest_extras[REST_ERROR_MAP_TYPES_EXTRA] = dict(error_map)
                # Whether the route is served through the REST processing
                # (the default) or opted out of it.
                record_rest_processing(rest_extras, merged_rest_processing)
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
        parent_placement: Optional[EndpointDescriptor] = None,
        **kwargs
    ) -> EndpointDescriptor:
        """
            Attach a child endpoint relative to this endpoint's base path.
            
            This method creates a descriptor for the child endpoint with
            paths computed relative to the parent's base_path/base_leaf.
            Constraints are merged following inheritance rules.

            The descriptor returned is the *placement*: it records where the
            child sits and what it inherits. The routes themselves come from
            the child: every handler the child has declared with
            ``attach_at`` is re-placed under the placement, keeping its own
            handler, and recorded against this class -- see
            :meth:`_place_child_handlers`. Declare a child's handlers before
            attaching it.
            
            Nested attachment: when this endpoint was itself attached to a
            parent, pass the descriptor that attachment returned as
            ``parent_placement``. The child is then composed under that
            placement's path -- which already carries every prefix from the
            root down -- instead of under this endpoint's own base, and it
            inherits the placement's merged constraints, tags and version
            instead of this class's own. Without ``parent_placement`` the
            behavior is the single-level one described above.
            
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
            :param parent_placement: The descriptor this endpoint received
                when it was attached to its own parent. When given, the
                child is placed under that descriptor's path and inherits
                its constraints, tags and version.
            :param kwargs: Additional overrides for child descriptor.
            
            :returns: The merged EndpointDescriptor for the child.
            
            :raises EndpointRegistrationError: If ``parent_placement`` has
                neither a path nor a leaf to compose under.
        """
        # Determine child's leaf/path
        child_leaf = leaf if leaf is not None else child_endpoint.base_leaf
        child_path = path if path is not None else child_endpoint.base_path
        
        # Determine what the child inherits from its parent: this class's
        # own attributes, or -- when this endpoint is nested under another
        # parent -- the placement that parent gave it, which already has the
        # prefixes and constraints of every level above.
        placement_base: Optional[str] = None
        if parent_placement is None:
            parent_version = cls.version
            parent_tags = list(cls.tags)
            parent_constraints = EndpointConstraints(
                access_policy=cls.access_policy,
                rate_limit=cls.rate_limit,
                scopes=cls.access_policy.scopes if cls.access_policy else [],
                roles=cls.access_policy.roles if cls.access_policy else []
            )
        else:
            placement_base = cls._placement_base_path(parent_placement)
            parent_version = parent_placement.version
            parent_tags = list(parent_placement.tags)
            parent_constraints = parent_placement.constraints
        
        # Compute the final path relative to parent's base
        if parent_placement is None:
            final_path = cls._compute_child_path(child_leaf, child_path)
        else:
            final_path = cls._compute_child_path_from_base(
                parent_base=placement_base,
                child_leaf=child_leaf,
                child_path=child_path
            )
        
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
            merged_version = parent_version
        
        # Merge tags
        child_tags = tags if tags is not None else list(child_endpoint.tags)
        if merge_tags:
            # Parent tags appended to child tags
            merged_tags = list(child_tags)
            for tag in parent_tags:
                if tag not in merged_tags:
                    merged_tags.append(tag)
        else:
            # Child tags win (default behavior)
            merged_tags = child_tags if child_tags else list(parent_tags)
        
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
        
        # Record the base a nested child was composed under
        if parent_placement is not None:
            extras_dict[ENDPOINT_PARENT_PLACEMENT_EXTRA] = placement_base
        
        # The placement descriptor says where the child was placed and what
        # it inherits. It is not itself a route, so it gets a stand-in
        # handler that explains that if anything ever calls it.
        placement_handler = cls._make_placement_handler(child_endpoint)

        # Create the descriptor
        descriptor = EndpointDescriptor(
            handler=placement_handler,
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

        # Re-place the child's own handlers under the placement and record
        # them against this class, so `cls.register()` returns routes that
        # serve the child's real handlers.
        cls._place_child_handlers(
            child_endpoint=child_endpoint,
            placement=descriptor,
            merge_tags=merge_tags,
            replace_scopes=replace_scopes,
            replace_roles=replace_roles
        )

        return descriptor

    @classmethod
    def _make_placement_handler(cls, child_endpoint: Type["Endpoint"]) -> Callable[..., Any]:
        """
            Build the stand-in handler carried by a placement descriptor.

            A placement has no handler of its own: the child's handlers are
            re-placed under it by :meth:`_place_child_handlers`. If a
            placement is routed anyway -- the child declared no handlers, so
            there was nothing to re-place -- a request for it fails with an
            error that names the child, instead of an unrelated TypeError.

            :param child_endpoint: The child endpoint class being attached.

            :returns: The stand-in handler, marked with
                      :data:`UNROUTED_PLACEMENT_ATTR`.
        """
        def placement_handler(request: Any = None) -> None:
            errmsg_lines = [
                f"No handler is attached for the child endpoint '{child_endpoint.__name__}'.",
                "attach_child() re-places the handlers a child declares with attach_at(); "
                f"'{child_endpoint.__name__}' declared none before it was attached.",
            ]
            errmsg = os.linesep.join(errmsg_lines)
            raise EndpointRegistrationError(
                message=errmsg,
                endpoint=child_endpoint,
                missing_fields=["handler"]
            )

        placement_handler.__name__ = f"{child_endpoint.__name__}_child"
        placement_handler.__module__ = child_endpoint.__module__
        setattr(placement_handler, UNROUTED_PLACEMENT_ATTR, True)

        return placement_handler

    @classmethod
    def _place_child_handlers(
        cls,
        child_endpoint: Type["Endpoint"],
        placement: EndpointDescriptor,
        merge_tags: bool = False,
        replace_scopes: bool = False,
        replace_roles: bool = False
    ) -> List[EndpointDescriptor]:
        """
            Re-place the handlers a child endpoint declared under the path
            its parent placed it at.

            Each descriptor the child declared (see
            :meth:`routable_descriptors`) yields a new descriptor that keeps
            the child's handler, methods, documentation and extras, moves the
            path under the placement, and merges the placement's constraints,
            tags and version with the handler's own. The new descriptors are
            recorded against this class, so ``cls.register()`` returns them.
            The child's own descriptors are not changed: the child can still
            be served at its own path, or attached to another parent.

            Only the handlers the child has declared when this is called are
            re-placed; attach a child after its handlers are defined.

            :param child_endpoint: The child endpoint class being attached.
            :param placement: The placement descriptor built by
                              ``attach_child`` for this child.
            :param merge_tags: If True, the placement's tags are appended to
                               each handler's tags.
            :param replace_scopes: If True, a handler's scopes replace the
                                   placement's instead of accumulating.
            :param replace_roles: If True, a handler's roles replace the
                                  placement's instead of accumulating.

            :returns: The re-placed descriptors, in declaration order.
        """
        rtnval: List[EndpointDescriptor] = []

        if not hasattr(child_endpoint, "routable_descriptors"):
            return rtnval

        placement_path = placement.path
        if placement_path is None and placement.leaf is not None:
            placement_path = f"/{placement.leaf}"
        if placement_path is None:
            placement_path = "/"

        child_base: Optional[str] = None
        child_base_path = getattr(child_endpoint, "base_path", None)
        child_base_leaf = getattr(child_endpoint, "base_leaf", None)
        if child_base_path is not None:
            child_base = "/" + child_base_path.strip("/")
        elif child_base_leaf is not None:
            child_base = "/" + child_base_leaf.strip("/")

        for child_descriptor in child_endpoint.routable_descriptors():
            if getattr(child_descriptor.handler, UNROUTED_PLACEMENT_ATTR, False) is True:
                # A placement the child holds for a handler-less child of
                # its own; there is nothing behind it to serve.
                continue

            placed_path = cls._compute_placed_path(
                placement_path=placement_path,
                child_base=child_base,
                child_descriptor=child_descriptor
            )

            merged_policy = ConstraintMerger.merge_access_policies(
                parent=placement.constraints.access_policy,
                child=child_descriptor.constraints.access_policy,
                replace_roles=replace_roles,
                replace_scopes=replace_scopes
            )
            merged_rate_limit = ConstraintMerger.merge_rate_limits(
                parent=placement.constraints.rate_limit,
                child=child_descriptor.constraints.rate_limit
            )
            placed_constraints = EndpointConstraints(
                access_policy=merged_policy,
                rate_limit=merged_rate_limit,
                scopes=merged_policy.scopes if merged_policy else [],
                roles=merged_policy.roles if merged_policy else []
            )

            placed_tags = ConstraintMerger.merge_tags(
                parent=list(placement.tags),
                child=list(child_descriptor.tags),
                merge=merge_tags,
                replace=False
            )

            placed_version = child_descriptor.version
            if placed_version is None:
                placed_version = placement.version

            placed_extras: Dict[str, Any] = dict(child_descriptor.extras)
            placed_extras[ENDPOINT_PARENT_PLACEMENT_EXTRA] = placement_path.rstrip("/")

            placed = EndpointDescriptor(
                handler=child_descriptor.handler,
                module=child_descriptor.module,
                leaf=None,
                path=placed_path,
                methods=list(child_descriptor.methods),
                version=placed_version,
                tags=placed_tags,
                constraints=placed_constraints,
                doc=child_descriptor.doc,
                extras=placed_extras,
                on_conflict=child_descriptor.on_conflict
            )

            declare_on_class(cls, placed)
            rtnval.append(placed)

        return rtnval

    @staticmethod
    def _compute_placed_path(
        placement_path: str,
        child_base: Optional[str],
        child_descriptor: EndpointDescriptor
    ) -> str:
        """
            Compute where a child's handler lives once the child is placed.

            The handler keeps its position relative to the child: the child's
            own base prefix, when the handler's path carries it, is replaced
            by the placement path. A handler declared ``absolute=True``, or
            one already under the placement path, keeps its path.

            :param placement_path: The path the child was placed at.
            :param child_base: The child's own base path with a leading
                               slash and no trailing one, or None.
            :param child_descriptor: The descriptor the child declared.

            :returns: The path of the re-placed handler.
        """
        declared_path = child_descriptor.path
        if declared_path is None and child_descriptor.leaf is not None:
            declared_path = f"/{child_descriptor.leaf}"
        if declared_path is None:
            declared_path = "/"
        if not declared_path.startswith("/"):
            declared_path = f"/{declared_path}"

        if child_descriptor.extras.get("absolute") is True:
            return declared_path

        placement_base = placement_path.rstrip("/")

        if declared_path == placement_base or declared_path.startswith(f"{placement_base}/"):
            return declared_path

        relative_path = declared_path
        if child_base is not None:
            if declared_path == child_base:
                relative_path = ""
            elif declared_path.startswith(f"{child_base}/"):
                relative_path = declared_path[len(child_base):]

        if relative_path == "/":
            relative_path = ""

        rtnval = f"{placement_base}{relative_path}"
        if len(rtnval) == 0:
            rtnval = "/"

        return rtnval

    @classmethod
    def _placement_base_path(cls, parent_placement: EndpointDescriptor) -> str:
        """
            Get the base path a nested child is composed under.
            
            The base is the path of ``parent_placement`` -- the descriptor
            this endpoint received when it was attached to its own parent --
            or ``/<leaf>`` when that descriptor carries only a leaf. A
            trailing slash is removed, as it is from ``base_path``.
            
            :param parent_placement: The descriptor this endpoint received
                                     when it was attached to its parent.
            
            :returns: The base path for the nested child.
            
            :raises EndpointRegistrationError: If the placement has neither
                a path nor a leaf.
        """
        if parent_placement.path is not None:
            placement_path = parent_placement.path
        elif parent_placement.leaf is not None:
            placement_path = f"/{parent_placement.leaf}"
        else:
            errmsg_lines = [
                f"Cannot attach a child to '{cls.__name__}' under its parent placement:",
                "the 'parent_placement' descriptor has neither a 'path' nor a 'leaf'.",
                "Pass the descriptor that attach_child() returned when "
                f"'{cls.__name__}' was attached to its parent.",
            ]
            errmsg = os.linesep.join(errmsg_lines)
            raise EndpointRegistrationError(
                message=errmsg,
                endpoint=cls,
                missing_fields=["path", "leaf"]
            )
        
        base_path = placement_path.rstrip("/")
        return base_path
    
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
        
        rtnval = cls._compute_child_path_from_base(
            parent_base=parent_base,
            child_leaf=child_leaf,
            child_path=child_path
        )
        return rtnval
    
    @classmethod
    def _compute_child_path_from_base(
        cls,
        parent_base: Optional[str],
        child_leaf: Optional[str],
        child_path: Optional[str]
    ) -> Optional[str]:
        """
            Compute the final path for a child endpoint under a given base.
            
            :param parent_base: The parent's base path, or None when the
                                parent has no base.
            :param child_leaf: The child's leaf segment.
            :param child_path: The child's path.
            
            :returns: The computed path, or None if no path can be computed.
        """
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

            Field annotations are resolved first, so postponed annotations
            (``from __future__ import annotations``), PEP 604 unions and
            nested dataclasses are described by their real types.

            :param schema: The dataclass type to convert.

            :returns: Dictionary containing JSON schema information.
        """
        rtnval = dataclass_to_json_schema(schema)
        return rtnval

    @classmethod
    def _type_to_schema(cls, field_type: Any) -> Dict[str, Any]:
        """
            Convert a Python type to a JSON schema type.

            :param field_type: The Python type to convert.

            :returns: Dictionary containing JSON schema type information.
        """
        rtnval = type_to_json_schema(field_type)
        return rtnval
