"""
    .. module:: middlewareregistry
        :platform: Darwin, Linux, Unix, Windows
        :synopsis: Central registry for scoped middleware management.

    .. moduleauthor:: Code Craft AI LLC

    This module provides the MiddlewareRegistry class that collects, orders,
    and provides access to all registered middleware across scopes (global,
    blueprint, route). The registry composes effective pipelines per-request
    by combining global, blueprint, and route middleware in that order.
"""

__author__ = "Code Craft AI LLC"
__copyright__ = "Copyright 2025, Code Craft AI LLC"
__credits__ = []

from typing import Any, Callable, Dict, List, Optional, Union

from ccai.webworks.routing.middleware import (
    Middleware,
    MiddlewareEntry,
    MiddlewarePipeline,
    _validate_middleware,
)
from ccai.webworks.routing.middlewarefactory import create_middleware
from ccai.webworks.routing.request import Request
from ccai.webworks.routing.response import Response


VALID_SCOPES = ("global", "blueprint", "route")


class MiddlewareRegistry:
    """
        Central registry that collects, orders, and provides access to
        all registered middleware across scopes.

        The registry manages three scopes:

        - **global**: Middleware applied to all requests.
        - **blueprint**: Middleware applied to all routes within a specific Blueprint.
        - **route**: Middleware applied to a single endpoint.

        When composing an effective pipeline for a request, the registry
        combines global middleware first, then blueprint middleware, then
        route middleware.
    """

    def __init__(self):
        """
            Construct a MiddlewareRegistry with empty storage for each scope.
        """
        self._global: List[MiddlewareEntry] = []
        self._blueprint: Dict[str, List[MiddlewareEntry]] = {}
        self._route: Dict[str, List[MiddlewareEntry]] = {}
        self._extension_components: Dict[str, List[Any]] = {}
        return

    def register(
        self,
        middleware: Union[Middleware, Callable[[Request, Callable[[Request], Response]], Response]],
        name: Optional[str] = None,
        scope: str = "global",
        scope_key: Optional[str] = None,
        priority: int = 50,
        position: str = "end",
        factory: Optional[Callable] = None,
        factory_config: Optional[Dict[str, Any]] = None
    ) -> None:
        """
            Register middleware at a given scope.

            When a ``factory`` is provided, it is invoked (with optional
            ``factory_config`` kwargs) via ``create_middleware`` to produce
            the middleware instance. The ``middleware`` parameter is ignored
            in this case.

            :param middleware: The middleware callable. Ignored when ``factory``
                is provided.
            :param name: Optional name for the middleware.
            :param scope: One of "global", "blueprint", "route".
            :param scope_key: Blueprint name or route path for scoped middleware.
                Required when scope is "blueprint" or "route".
            :param priority: Numeric priority (lower executes first). Default is 50.
            :param position: Positional hint ("start", "end", "before:<name>",
                "after:<name>"). Default is "end".
            :param factory: Optional factory callable that produces a middleware
                instance. When provided, ``create_middleware`` is used to
                instantiate and validate the middleware.
            :param factory_config: Optional keyword arguments passed to the
                factory callable. Only used when ``factory`` is provided.

            :raises TypeError: If middleware does not conform to the Middleware
                or AsyncMiddleware protocol and is not a valid callable.
            :raises ValueError: If scope is not one of the valid scopes, or
                if scope_key is missing for blueprint/route scopes.
        """
        if factory is not None:
            config_kwargs = factory_config if factory_config is not None else {}
            middleware = create_middleware(factory, **config_kwargs)
        
        _validate_middleware(middleware)

        if scope not in VALID_SCOPES:
            raise ValueError(
                f"Invalid scope '{scope}'. Must be one of {VALID_SCOPES}."
            )

        if scope in ("blueprint", "route") and not scope_key:
            raise ValueError(
                f"scope_key is required when scope is '{scope}'."
            )

        entry = MiddlewareEntry(middleware, name, priority=priority, scope=scope)

        target_list = self._get_scope_list(scope, scope_key)
        self._insert_entry(target_list, entry, position)
        return

    def _get_scope_list(
        self,
        scope: str,
        scope_key: Optional[str] = None
    ) -> List[MiddlewareEntry]:
        """
            Get the entry list for a given scope and key, creating it if needed.

            :param scope: The middleware scope.
            :param scope_key: The scope key for blueprint/route scopes.

            :returns: The list of MiddlewareEntry objects for the scope.
        """
        if scope == "global":
            rtnval = self._global
        elif scope == "blueprint":
            if scope_key not in self._blueprint:
                self._blueprint[scope_key] = []
            rtnval = self._blueprint[scope_key]
        else:
            if scope_key not in self._route:
                self._route[scope_key] = []
            rtnval = self._route[scope_key]
        return rtnval

    def _insert_entry(
        self,
        entries: List[MiddlewareEntry],
        entry: MiddlewareEntry,
        position: str
    ) -> None:
        """
            Insert a MiddlewareEntry into a list at the specified position,
            respecting priority ordering within positional groups.

            :param entries: The target list of entries.
            :param entry: The entry to insert.
            :param position: Positional hint.

            :raises ValueError: If position references a missing name or is invalid.
        """
        priority = entry.priority

        if position == "end":
            insert_idx = len(entries)
            while insert_idx > 0 and entries[insert_idx - 1].priority > priority:
                insert_idx -= 1
            entries.insert(insert_idx, entry)
        elif position == "start":
            insert_idx = 0
            while insert_idx < len(entries) and entries[insert_idx].priority < priority:
                insert_idx += 1
            entries.insert(insert_idx, entry)
        elif position.startswith("before:"):
            target_name = position[7:]
            index = self._find_index_by_name(entries, target_name)
            if index is None:
                raise ValueError(
                    f"Middleware '{target_name}' not found in registry scope"
                )
            entries.insert(index, entry)
        elif position.startswith("after:"):
            target_name = position[6:]
            index = self._find_index_by_name(entries, target_name)
            if index is None:
                raise ValueError(
                    f"Middleware '{target_name}' not found in registry scope"
                )
            entries.insert(index + 1, entry)
        else:
            raise ValueError(f"Invalid position: {position}")
        return

    def _find_index_by_name(
        self,
        entries: List[MiddlewareEntry],
        name: str
    ) -> Optional[int]:
        """
            Find the index of a middleware entry by name.

            :param entries: The list of entries to search.
            :param name: The middleware name to find.

            :returns: The index of the entry, or None if not found.
        """
        rtnval = None
        for idx, entry in enumerate(entries):
            if entry.name == name:
                rtnval = idx
                break
        return rtnval


    def get_middleware_by_scope(
        self,
        scope: str,
        scope_key: Optional[str] = None
    ) -> List[MiddlewareEntry]:
        """
            Query registered middleware by scope.

            :param scope: The scope to query ("global", "blueprint", "route").
            :param scope_key: The scope key for blueprint/route scopes.

            :returns: A list of MiddlewareEntry objects registered at the
                specified scope and key.
        """
        if scope == "global":
            rtnval = list(self._global)
        elif scope == "blueprint":
            rtnval = list(self._blueprint.get(scope_key, []))
        elif scope == "route":
            rtnval = list(self._route.get(scope_key, []))
        else:
            rtnval = []
        return rtnval

    def compose_pipeline(
        self,
        blueprint_name: Optional[str] = None,
        route_path: Optional[str] = None
    ) -> MiddlewarePipeline:
        """
            Compose the effective pipeline for a request by combining
            global, then blueprint, then route middleware.

            :param blueprint_name: The blueprint name for blueprint-scoped
                middleware. None if no blueprint applies.
            :param route_path: The route path for route-scoped middleware.
                None if no route applies.

            :returns: A MiddlewarePipeline containing all applicable middleware
                in the correct execution order.
        """
        pipeline = MiddlewarePipeline()

        # Add global middleware first
        for entry in self._global:
            pipeline.add(
                entry.middleware,
                name=entry.name,
                priority=entry.priority,
                scope=entry.scope,
            )

        # Add blueprint middleware second
        if blueprint_name is not None:
            for entry in self._blueprint.get(blueprint_name, []):
                pipeline.add(
                    entry.middleware,
                    name=entry.name,
                    priority=entry.priority,
                    scope=entry.scope,
                )

        # Add route middleware last
        if route_path is not None:
            for entry in self._route.get(route_path, []):
                pipeline.add(
                    entry.middleware,
                    name=entry.name,
                    priority=entry.priority,
                    scope=entry.scope,
                )

        return pipeline


    def list_by_scope(self) -> Dict[str, List[MiddlewareEntry]]:
        """
            List all registered middleware grouped by scope.

            :returns: A dictionary where each scope key maps to the list
                of middleware registered at that scope. Blueprint and route
                scopes are flattened into their respective top-level keys.
        """
        rtnval: Dict[str, List[MiddlewareEntry]] = {}

        if self._global:
            rtnval["global"] = list(self._global)

        for bp_name, entries in self._blueprint.items():
            key = f"blueprint:{bp_name}"
            if entries:
                rtnval[key] = list(entries)

        for route_path, entries in self._route.items():
            key = f"route:{route_path}"
            if entries:
                rtnval[key] = list(entries)

        return rtnval

    def export_effective_pipeline(
        self,
        route_path: str,
        blueprint_name: Optional[str] = None
    ) -> List[str]:
        """
            Export the effective pipeline for a given route path as an
            ordered list of middleware names.

            :param route_path: The route path to compose the pipeline for.
            :param blueprint_name: Optional blueprint name for blueprint-scoped
                middleware.

            :returns: An ordered list of middleware names matching the
                composition order from compose_pipeline().
        """
        pipeline = self.compose_pipeline(
            blueprint_name=blueprint_name,
            route_path=route_path,
        )
        rtnval = pipeline.get_names()
        return rtnval

    def get_registered_components(self, hook_name: str) -> List[Any]:
        """
            Retrieve all middleware registered via the extensibility system
            for a given hook name.

            :param hook_name: The extensibility hook name to query.

            :returns: A list of middleware components registered via the
                specified hook.
        """
        rtnval = list(self._extension_components.get(hook_name, []))
        return rtnval

    def register_extension_component(
        self,
        hook_name: str,
        component: Any
    ) -> None:
        """
            Register a middleware component from the extensibility system.

            :param hook_name: The extensibility hook name.
            :param component: The middleware component to register.
        """
        if hook_name not in self._extension_components:
            self._extension_components[hook_name] = []
        self._extension_components[hook_name].append(component)
        return

    def __repr__(self) -> str:
        """
            Get string representation.

            :returns: String representation showing scope counts.
        """
        bp_count = sum(len(entries) for entries in self._blueprint.values())
        rt_count = sum(len(entries) for entries in self._route.values())
        rtnval = (
            f"MiddlewareRegistry(global={len(self._global)}, "
            f"blueprint={bp_count}, route={rt_count})"
        )
        return rtnval
