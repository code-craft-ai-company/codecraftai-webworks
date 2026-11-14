"""
.. module:: registry
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: Module-level registry for collecting endpoint descriptors.

.. moduleauthor:: Code Craft AI LLC
"""

__author__ = "Code Craft AI LLC"
__copyright__ = "Copyright 2025, Code Craft AI LLC"
__credits__ = []

import csv
import dataclasses
import inspect
import io
import json
from typing import Any, Dict, List, Optional, Tuple

from ccai.webworks.endpoints.descriptor import (
    ENDPOINT_DESCRIPTORS_ATTR,
    EndpointDescriptor
)


class EndpointConflictError(Exception):
    """
        Raised when two descriptors target the same path+method combination.
        
        This exception provides detailed information about the conflict,
        including the path, method, and both handlers involved.
        
        :param path: The conflicting URL path.
        :param method: The conflicting HTTP method.
        :param existing_handler: The handler already registered at this location.
        :param new_handler: The handler attempting to register at this location.
    """
    
    def __init__(
        self,
        path: str,
        method: str,
        existing_handler: Any,
        new_handler: Any
    ):
        self.path = path
        self.method = method
        self.existing_handler = existing_handler
        self.new_handler = new_handler
        
        existing_name = self._get_handler_name(existing_handler)
        new_name = self._get_handler_name(new_handler)
        
        message = (
            f"Conflict at {method} {path}: "
            f"existing={existing_name}, new={new_name}"
        )
        super().__init__(message)
    
    @staticmethod
    def _get_handler_name(handler: Any) -> str:
        """
            Get a displayable name for a handler.
            
            :param handler: The handler callable.
            
            :returns: String representation of the handler.
        """
        if hasattr(handler, "__module__") and hasattr(handler, "__name__"):
            return f"{handler.__module__}.{handler.__name__}"
        elif hasattr(handler, "__name__"):
            return handler.__name__
        else:
            return str(handler)


class EndpointRegistry:
    """
        The set of endpoints belonging to one application.

        A registry is an ordinary object and owns its own state. Build one,
        collect the modules whose endpoints belong to it, and hand it to the
        application::

            registry = EndpointRegistry()
            registry.collect_from(helloworld.endpoints)
            app = WebApplication(registry=registry)

        This used to be class-level state with every method a classmethod,
        which made the endpoint map process-global. Two applications in one
        process shared it, so importing a second one raised
        EndpointConflictError for routes that were never actually in conflict
        -- they simply belonged to different applications. Python's module
        cache made that unfixable from the outside: a module of handlers
        registers on first import and never again, so whichever registry was
        active at that moment kept them forever.

        Conflict detection is kept, and now means what it says: two handlers
        claiming the same path and method *within one application*.
    """

    def __init__(self) -> None:
        self._descriptors: List[EndpointDescriptor] = []
        self._path_method_index: Dict[Tuple[str, str], EndpointDescriptor] = {}

        # Every descriptor collect_from() has handed to register(), including
        # ones later replaced or narrowed. Re-collecting a source must be a
        # no-op for each of them, and the registered list alone cannot say
        # so once a descriptor has been replaced. The objects are held (not
        # just their ids) so an id cannot be reused by a new descriptor.
        self._collected: List[EndpointDescriptor] = []
        return

    def register(
        self,
        descriptor: EndpointDescriptor,
        on_conflict: str = "error"
    ) -> None:
        """
            Register a descriptor, checking for conflicts.
            
            This method adds an endpoint descriptor to the registry,
            checking for conflicts with existing registrations. If a
            conflict is detected and on_conflict is "error", an
            EndpointConflictError is raised. If on_conflict is "replace",
            the existing registration is replaced.
            
            :param descriptor: The EndpointDescriptor to register.
            :param on_conflict: "error" to raise on conflict, "replace" to override.
            
            :raises EndpointConflictError: If path+method already registered
                                          and on_conflict="error".
        """
        # Determine the path for indexing
        path = self._get_index_path(descriptor)

        keys: List[Tuple[str, str]] = []
        for method in descriptor.methods:
            key = (path, method.upper())
            if key not in keys:
                keys.append(key)

        # Check every method before changing anything. A descriptor is
        # registered for all of its methods or for none of them: stopping at
        # the second method of three used to leave the first one indexed
        # against a descriptor that was never added.
        if on_conflict != "replace":
            for key in keys:
                existing = self._path_method_index.get(key)
                if existing is not None:
                    raise EndpointConflictError(
                        path=key[0],
                        method=key[1],
                        existing_handler=existing.handler,
                        new_handler=descriptor.handler
                    )

        # Take each contested method away from the descriptor that holds it
        for key in keys:
            if key in self._path_method_index:
                self._release_key(key)

        # Register the new descriptor for each of its methods
        for key in keys:
            self._path_method_index[key] = descriptor

        # Add to the descriptors list
        self._descriptors.append(descriptor)

        return
    
    def _get_index_path(self, descriptor: EndpointDescriptor) -> str:
        """
            Get the path to use for indexing a descriptor.
            
            :param descriptor: The descriptor to get the path for.
            
            :returns: The path string for indexing.
        """
        if descriptor.path is not None:
            return descriptor.path
        elif descriptor.leaf is not None:
            return f"/{descriptor.leaf}"
        else:
            return "/"
    
    def _release_key(self, key: Tuple[str, str]) -> None:
        """
            Take one ``(path, method)`` away from the descriptor registered
            for it, leaving that descriptor's other methods in place.

            When the descriptor serves other methods as well, it is swapped
            for a copy that lists only the methods it still holds, and the
            index entries for those methods are pointed at the copy. The
            original object is not modified: it is the mark on a handler and
            may be registered in another application's registry. When the
            released method was its last, the descriptor is removed.

            :param key: The (path, method) tuple to release.
        """
        existing = self._path_method_index.pop(key, None)
        if existing is None:
            return

        path, released_method = key

        remaining_methods = [
            method for method in existing.methods
            if method.upper() != released_method
        ]

        position: Optional[int] = None
        for index, candidate in enumerate(self._descriptors):
            if candidate is existing:
                position = index
                break

        if len(remaining_methods) == 0:
            if position is not None:
                self._descriptors.pop(position)
            return

        narrowed = dataclasses.replace(existing, methods=remaining_methods)

        if position is not None:
            self._descriptors[position] = narrowed
        else:
            self._descriptors.append(narrowed)

        for method in remaining_methods:
            remaining_key = (path, method.upper())
            if self._path_method_index.get(remaining_key) is existing:
                self._path_method_index[remaining_key] = narrowed

        return
    
    def collect(self) -> List[EndpointDescriptor]:
        """
            Return all registered descriptors.

            This method returns a copy of the internal descriptors list
            to prevent external modification of the registry state.

            :returns: List of all EndpointDescriptor objects.
        """
        return self._descriptors.copy()

    def update_descriptor_path(
        self,
        descriptor: EndpointDescriptor,
        new_path: str,
    ) -> None:
        """
            Update an already-registered descriptor's ``path`` and move
            its entries in the ``(path, method)`` lookup index.

            This helper exists to support deferred path resolution from
            :meth:`Blueprint.__init_subclass__`: when a subclass-body
            decorator is invoked against a *parent* class (so the
            originally-registered path is missing the subclass's
            ``base_path`` prefix), the subclass corrects the path after
            it is fully defined.

            The descriptor object identity is preserved so any holder of
            the reference (the registry, blueprint caches, the OpenAPI
            generator) sees the updated path immediately.

            ``leaf`` is cleared because once an explicit ``path`` is
            assigned the registry's index uses the path directly.

            :param descriptor: The :class:`EndpointDescriptor` to mutate.
                               Must already be in the registry; raises
                               ``ValueError`` otherwise.
            :param new_path: Replacement path string.

            :raises ValueError: When *descriptor* is not in the registry.
            :raises EndpointConflictError: When ``(new_path, method)``
                                           already maps to a different
                                           descriptor for any of the
                                           descriptor's methods.
        """
        if descriptor not in self._descriptors:
            errmsg = (
                "Cannot update path for a descriptor that is not "
                "registered: handler={!r}, current_path={!r}".format(
                    descriptor.handler,
                    descriptor.path,
                )
            )
            raise ValueError(errmsg)

        old_index_path = self._get_index_path(descriptor)
        new_index_path = new_path

        # Short-circuit when the path is unchanged. Avoids touching the
        # index for the no-op case.
        if old_index_path == new_index_path:
            descriptor.path = new_path
            descriptor.leaf = None
            return

        # Validate first — if any of the new keys conflict with a
        # different descriptor, abort before mutating any state.
        for method in descriptor.methods:
            new_key = (new_index_path, method.upper())
            existing = self._path_method_index.get(new_key)
            if existing is not None and existing is not descriptor:
                raise EndpointConflictError(
                    path=new_index_path,
                    method=method.upper(),
                    existing_handler=existing.handler,
                    new_handler=descriptor.handler,
                )

        # All clear — remove old index keys, mutate the descriptor,
        # install new index keys.
        for method in descriptor.methods:
            old_key = (old_index_path, method.upper())
            if self._path_method_index.get(old_key) is descriptor:
                del self._path_method_index[old_key]

        descriptor.path = new_path
        descriptor.leaf = None

        for method in descriptor.methods:
            new_key = (new_index_path, method.upper())
            self._path_method_index[new_key] = descriptor

        return
    
    def collect_from(self, *sources: Any, on_conflict: Optional[str] = None) -> int:
        """
            Register every marked handler found in the given sources.

            :meth:`Endpoint.attach_at` only marks a handler; this is the step
            that puts it in an application's endpoint map. A source may be a
            module or package, a class, or a single callable, so an
            application can collect a whole site while a test collects one
            handler it just defined::

                registry.collect_from(helloworld.endpoints)
                registry.collect_from(StatusEndpoint, some_handler)

            Modules are walked one level: their classes are descended into,
            so handlers defined in a class body are found, but imported
            submodules are not followed. Collecting the same source twice
            registers each descriptor once -- re-collection is not a second
            registration and does not self-conflict.

            :param sources: Modules, classes or callables to scan.
            :param on_conflict: Overrides the policy each descriptor declared
                                at its decorator. Left as None normally.

            :returns: The number of descriptors newly registered.
        """
        found: List[EndpointDescriptor] = []

        for source in sources:
            self._gather(source, found)

        # Leave out what this registry already holds or was already given.
        pending: List[EndpointDescriptor] = []
        for descriptor in found:
            if self._was_collected(descriptor) or self._is_pending(descriptor, pending):
                continue
            pending.append(descriptor)

        # Register the descriptors that claim their route outright before the
        # ones declared ``on_conflict="replace"``. An override then replaces
        # the handler it overrides whichever of the two was found first, so
        # the outcome does not depend on how the functions are named or on
        # the order the sources are listed in.
        ordered: List[Tuple[EndpointDescriptor, str]] = []
        overrides: List[Tuple[EndpointDescriptor, str]] = []
        for descriptor in pending:
            policy = on_conflict if on_conflict is not None else descriptor.on_conflict
            if policy == "replace":
                overrides.append((descriptor, policy))
            else:
                ordered.append((descriptor, policy))
        ordered.extend(overrides)

        count = 0
        for descriptor, policy in ordered:
            self.register(descriptor, on_conflict=policy)
            self._collected.append(descriptor)
            count += 1

        return count

    def _was_collected(self, descriptor: EndpointDescriptor) -> bool:
        """
            Whether this registry holds ``descriptor`` or was already given
            it by an earlier :meth:`collect_from`.

            :param descriptor: The descriptor to look for (by identity).

            :returns: True when the descriptor has been seen before.
        """
        for candidate in self._descriptors:
            if candidate is descriptor:
                return True

        for candidate in self._collected:
            if candidate is descriptor:
                return True

        return False

    @staticmethod
    def _is_pending(descriptor: EndpointDescriptor, pending: List[EndpointDescriptor]) -> bool:
        """
            Whether ``descriptor`` is already in the list being collected.

            :param descriptor: The descriptor to look for (by identity).
            :param pending: The descriptors gathered so far in this call.

            :returns: True when the same descriptor object is in ``pending``.
        """
        for candidate in pending:
            if candidate is descriptor:
                return True

        return False

    def _gather(self, source: Any, found: List[EndpointDescriptor]) -> None:
        """
            Append every descriptor marked on ``source`` to ``found``.

            Members are visited in definition order, not by name: the order
            handlers are written in is the order they are registered in.

            A class that is itself the source contributes everything declared
            through it, free functions included (``cls.attach_at(...)`` at
            module level). A class met while walking a module contributes
            only the handlers written in its body -- the free functions
            declared through it are members of their own module and are
            collected from there, and a module that merely imports ``Endpoint``
            must not pull in every endpoint declared through that shared base.

            :param source: A module, class or callable to inspect.
            :param found: Accumulator, appended to in place.
        """
        marks = getattr(source, ENDPOINT_DESCRIPTORS_ATTR, None)
        if marks is not None:
            found.extend(marks)
            return

        if inspect.isclass(source):
            found.extend(self._class_descriptors(source, include_declared=True))
            return

        if inspect.ismodule(source):
            for member in list(vars(source).values()):
                member_marks = getattr(member, ENDPOINT_DESCRIPTORS_ATTR, None)
                if member_marks is not None:
                    found.extend(member_marks)
                elif inspect.isclass(member):
                    found.extend(self._class_descriptors(member, include_declared=False))

        return

    @staticmethod
    def _class_descriptors(source: Any, include_declared: bool) -> List[EndpointDescriptor]:
        """
            The descriptors a class contributes to a collection.

            An endpoint class is asked through
            :meth:`Endpoint.routable_descriptors`, which walks the class in
            method-resolution and definition order and binds handlers written
            as instance methods. Any other class is searched for marked
            attributes directly.

            :param source: The class to inspect.
            :param include_declared: Include free functions declared through
                                     the class, when it is an endpoint class.

            :returns: The descriptors found, in definition order.
        """
        routable = getattr(source, "routable_descriptors", None)
        if routable is not None:
            rtnval: List[EndpointDescriptor] = list(routable(include_declared=include_declared))
            return rtnval

        rtnval = []
        seen: List[int] = []
        for klass in source.__mro__:
            for value in list(vars(klass).values()):
                handler = value
                if isinstance(handler, (classmethod, staticmethod)):
                    handler = handler.__func__
                for descriptor in getattr(handler, ENDPOINT_DESCRIPTORS_ATTR, None) or ():
                    if id(descriptor) in seen:
                        continue
                    seen.append(id(descriptor))
                    rtnval.append(descriptor)

        return rtnval

    def export_security_map(
        self,
        filter_tag: Optional[str] = None,
        format: str = "markdown"
    ) -> str:
        """
            Export security audit map for review.
            
            This method generates a formatted security map showing each
            endpoint's security posture. The map can be filtered by tag
            and exported in various formats.
            
            :param filter_tag: Optional tag to filter endpoints.
            :param format: Output format ("markdown", "csv", "json").
            
            :returns: Formatted security map string.
        """
        # Collect and filter descriptors
        descriptors = self._filter_descriptors(filter_tag)
        
        # Convert to security rows
        rows = [desc.to_security_row() for desc in descriptors]
        
        # Format based on requested format
        if format == "markdown":
            return self._format_markdown(rows)
        elif format == "csv":
            return self._format_csv(rows)
        elif format == "json":
            return self._format_json(rows)
        else:
            raise ValueError(f"Unsupported format: {format}")
    
    def _filter_descriptors(
        self,
        filter_tag: Optional[str]
    ) -> List[EndpointDescriptor]:
        """
            Filter descriptors by tag.
            
            :param filter_tag: Tag to filter by, or None for all.
            
            :returns: Filtered list of descriptors.
        """
        if filter_tag is None:
            return self._descriptors.copy()
        
        return [
            desc for desc in self._descriptors
            if filter_tag in desc.tags
        ]
    
    def _format_markdown(self, rows: List[Dict[str, Any]]) -> str:
        """
            Format security rows as a Markdown table.
            
            :param rows: List of security row dictionaries.
            
            :returns: Markdown formatted table string.
        """
        if not rows:
            return "No endpoints registered.\n"
        
        # Define columns
        columns = ["path", "methods", "handler", "access_policy", "scopes", "roles", "rate_limit", "summary"]
        
        # Build header
        header = "| " + " | ".join(columns) + " |"
        separator = "| " + " | ".join(["---"] * len(columns)) + " |"
        
        # Build rows
        table_rows = []
        for row in rows:
            values = []
            for col in columns:
                value = row.get(col)
                if value is None:
                    value = ""
                elif not isinstance(value, str):
                    value = str(value)
                # Escape pipe characters in values
                value = value.replace("|", "\\|")
                values.append(value)
            table_rows.append("| " + " | ".join(values) + " |")
        
        return "\n".join([header, separator] + table_rows) + "\n"
    
    def _format_csv(self, rows: List[Dict[str, Any]]) -> str:
        """
            Format security rows as CSV.
            
            :param rows: List of security row dictionaries.
            
            :returns: CSV formatted string.
        """
        if not rows:
            return ""
        
        # Define columns
        columns = ["path", "methods", "handler", "access_policy", "scopes", "roles", "rate_limit", "summary"]
        
        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=columns, extrasaction="ignore")
        writer.writeheader()
        
        for row in rows:
            # Convert None values to empty strings
            clean_row = {k: (v if v is not None else "") for k, v in row.items()}
            writer.writerow(clean_row)
        
        return output.getvalue()
    
    def _format_json(self, rows: List[Dict[str, Any]]) -> str:
        """
            Format security rows as JSON.
            
            :param rows: List of security row dictionaries.
            
            :returns: JSON formatted string.
        """
        return json.dumps(rows, indent=2)

