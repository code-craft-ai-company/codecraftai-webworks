"""
    Template context management module.
    
    This module provides the TemplateContext class for managing template
    context variables. The context provides a dictionary-like interface
    for storing and accessing variables passed to templates during rendering.
    
    The module also provides advanced variable resolution capabilities
    including nested dictionary access via dot notation, object attribute
    access, callable invocation, and list/sequence indexing.
    
    Additionally, this module provides:
    
    - GlobalContext: A singleton store for global variables available to all templates.
    - RequestContext: A context for request-scoped variables available during a single request.
    - ContextProcessorRegistry: A registry for context processor functions that add
      variables to every template context.
"""

from typing import Any, Callable, Dict, List, Optional, Sequence

from automojo.webworks.templating.exceptions import UndefinedVariableError


class TemplateContext:
    """
        Manages template context variables.
        
        The TemplateContext provides a dictionary-like interface for storing
        and accessing variables that are passed to templates during rendering.
        It supports standard dictionary operations like get, set, and contains,
        as well as methods for updating and merging contexts.
        
        Example usage::
        
            context = TemplateContext({"title": "Home"})
            context["user"] = "Alice"
            context.update({"items": [1, 2, 3]})
            
            if "title" in context:
                print(context["title"])
            
            # Merge with another context
            other = TemplateContext({"footer": "Copyright 2024"})
            merged = context.merge(other)
    """
    
    def __init__(
        self,
        initial: Optional[Dict[str, Any]] = None,
        undefined_behavior: Optional[str] = None
    ) -> None:
        """
            Construct a template context.

            :param initial: Initial context variables as a dictionary.
                If None, an empty context is created.
            :param undefined_behavior: How to handle undefined variables during
                resolution. Supported values:
                - None: Raise KeyError for missing keys (default, backward compatible).
                - "silent": Return an empty string for missing keys.
                - "strict": Raise UndefinedVariableError for missing keys.
        """
        self._data: Dict[str, Any] = {}
        self._undefined_behavior: Optional[str] = undefined_behavior
        if initial is not None:
            self._data.update(initial)
        return
    
    def __getitem__(self, key: str) -> Any:
        """
            Get a context variable.
            
            :param key: Variable name to retrieve.
            
            :returns: The value associated with the key.
            
            :raises KeyError: If the key does not exist in the context.
        """
        return self._data[key]
    
    def __setitem__(self, key: str, value: Any) -> None:
        """
            Set a context variable.
            
            :param key: Variable name to set.
            :param value: Value to associate with the key.
        """
        self._data[key] = value
        return
    
    def __contains__(self, key: str) -> bool:
        """
            Check if a variable exists in the context.
            
            :param key: Variable name to check.
            
            :returns: True if the key exists, False otherwise.
        """
        return key in self._data
    
    def get(self, key: str, default: Any = None) -> Any:
        """
            Get a context variable with a default value.
            
            :param key: Variable name to retrieve.
            :param default: Default value to return if the key is not found.
            
            :returns: The value associated with the key, or the default value
                if the key does not exist.
        """
        return self._data.get(key, default)
    
    def update(self, data: Dict[str, Any]) -> None:
        """
            Update context with multiple variables.
            
            :param data: Dictionary of variables to add or update in the context.
        """
        self._data.update(data)
        return
    
    def merge(self, other: "TemplateContext") -> "TemplateContext":
        """
            Merge with another context.

            Creates a new TemplateContext containing all variables from both
            this context and the other context. Variables from the other context
            take precedence when there are key conflicts. The undefined_behavior
            setting from the other context takes precedence if set, otherwise
            the setting from this context is used.

            :param other: Context to merge with this context.

            :returns: A new TemplateContext containing merged variables.
        """
        merged_data = dict(self._data)
        merged_data.update(other._data)

        # Use other's undefined_behavior if set, otherwise use self's
        behavior = other._undefined_behavior if other._undefined_behavior is not None else self._undefined_behavior

        return TemplateContext(merged_data, undefined_behavior=behavior)
    
    def to_dict(self) -> Dict[str, Any]:
        """
            Convert context to a dictionary.
            
            :returns: A copy of the context data as a dictionary.
        """
        return dict(self._data)
    
    def resolve(self, path: str) -> Any:
        """
            Resolve a dot-notation path to a value.

            This method supports multiple access patterns:

            - Nested dictionary access: "user.name" resolves to context["user"]["name"]
            - Object attribute access: "user.get_name" resolves to context["user"].get_name
            - Callable invocation: If a resolved value is callable, it is invoked
            - List/sequence indexing: "items.0" resolves to context["items"][0]

            The resolution order for each path segment is:
            1. Dictionary key access (if current value is a dict-like object)
            2. Sequence index access (if segment is numeric and value is a sequence)
            3. Object attribute access
            4. If the resolved value is callable, invoke it with no arguments

            When a path cannot be resolved, the behavior depends on the
            undefined_behavior setting:
            - None: Raise KeyError (default, backward compatible).
            - "silent": Return an empty string.
            - "strict": Raise UndefinedVariableError.

            :param path: Dot-notation path to resolve (e.g., "user.name", "items.0").

            :returns: The resolved value.

            :raises KeyError: If the path cannot be resolved and undefined_behavior is None.
            :raises UndefinedVariableError: If the path cannot be resolved and
                undefined_behavior is "strict".

            Example usage::

                context = TemplateContext({
                    "user": {"name": "Alice", "age": 30},
                    "items": [1, 2, 3],
                    "get_title": lambda: "Home"
                })

                context.resolve("user.name")      # Returns "Alice"
                context.resolve("items.0")        # Returns 1
                context.resolve("get_title")      # Returns "Home" (callable invoked)
        """
        if not path:
            raise KeyError("Empty path cannot be resolved")

        segments = path.split(".")

        try:
            current = self._resolve_segment(self._data, segments[0], path, 0)
        except KeyError:
            if self._undefined_behavior == "silent":
                return ""
            elif self._undefined_behavior == "strict":
                raise UndefinedVariableError(path)
            else:
                raise

        for index, segment in enumerate(segments[1:], start=1):
            try:
                current = self._resolve_segment(current, segment, path, index)
            except KeyError:
                if self._undefined_behavior == "silent":
                    return ""
                elif self._undefined_behavior == "strict":
                    raise UndefinedVariableError(path)
                else:
                    raise

        # If the final value is callable, invoke it
        if callable(current) and not isinstance(current, type):
            current = current()

        return current
    
    def _resolve_segment(
        self,
        current: Any,
        segment: str,
        full_path: str,
        segment_index: int
    ) -> Any:
        """
            Resolve a single segment of a dot-notation path.
            
            :param current: The current value to resolve the segment from.
            :param segment: The segment name to resolve.
            :param full_path: The full path being resolved (for error messages).
            :param segment_index: The index of this segment in the path (for error messages).
            
            :returns: The resolved value for this segment.
            
            :raises KeyError: If the segment cannot be resolved.
        """
        # Try dictionary-style access first
        if isinstance(current, dict):
            if segment in current:
                return current[segment]
            # Fall through to try other access methods
        
        # Try sequence index access if segment is numeric
        if segment.isdigit() or (segment.startswith("-") and segment[1:].isdigit()):
            index = int(segment)
            if isinstance(current, (list, tuple)):
                try:
                    return current[index]
                except IndexError:
                    raise KeyError(
                        f"Index {index} out of range for sequence at segment "
                        f"'{segment}' in path '{full_path}'"
                    )
        
        # Try object attribute access
        if hasattr(current, segment):
            value = getattr(current, segment)
            # If the attribute is callable (method), invoke it
            if callable(value) and not isinstance(value, type):
                return value()
            return value
        
        # If we get here, the segment could not be resolved
        raise KeyError(
            f"Cannot resolve segment '{segment}' (index {segment_index}) "
            f"in path '{full_path}'"
        )


class GlobalContext:
    """
        A singleton store for global template variables.
        
        GlobalContext provides a centralized location for variables that
        should be available to all templates. Global variables are merged
        into every TemplateContext before rendering.
        
        This class uses class-level storage so that all access points share
        the same set of global variables. Use the class methods to manage
        global variables.
        
        Example usage::
        
            GlobalContext.set("app_name", "My Application")
            GlobalContext.set("version", "1.0.0")
            
            # Retrieve a global variable
            name = GlobalContext.get("app_name")
            
            # Get all globals as a dictionary
            all_globals = GlobalContext.to_dict()
            
            # Clear all globals
            GlobalContext.clear()
    """
    
    _globals: Dict[str, Any] = {}
    
    @classmethod
    def set(cls, key: str, value: Any) -> None:
        """
            Set a global context variable.
            
            :param key: Variable name.
            :param value: Variable value.
        """
        cls._globals[key] = value
        return
    
    @classmethod
    def get(cls, key: str, default: Any = None) -> Any:
        """
            Get a global context variable.
            
            :param key: Variable name.
            :param default: Default value if the key is not found.
            
            :returns: The value associated with the key, or the default value.
        """
        return cls._globals.get(key, default)
    
    @classmethod
    def remove(cls, key: str) -> None:
        """
            Remove a global context variable.
            
            :param key: Variable name to remove.
            
            :raises KeyError: If the key does not exist.
        """
        del cls._globals[key]
        return
    
    @classmethod
    def contains(cls, key: str) -> bool:
        """
            Check if a global context variable exists.
            
            :param key: Variable name to check.
            
            :returns: True if the key exists, False otherwise.
        """
        return key in cls._globals
    
    @classmethod
    def update(cls, data: Dict[str, Any]) -> None:
        """
            Update global context with multiple variables.
            
            :param data: Dictionary of variables to add or update.
        """
        cls._globals.update(data)
        return
    
    @classmethod
    def to_dict(cls) -> Dict[str, Any]:
        """
            Get all global context variables as a dictionary.
            
            :returns: A copy of the global variables dictionary.
        """
        return dict(cls._globals)
    
    @classmethod
    def clear(cls) -> None:
        """
            Remove all global context variables.
        """
        cls._globals.clear()
        return


class RequestContext(TemplateContext):
    """
        A context for request-scoped template variables.
        
        RequestContext extends TemplateContext to provide variables that are
        available only during a single request. It supports merging with
        global context variables so that templates receive both global and
        request-specific data.
        
        Example usage::
        
            # Create a request context with request-specific data
            request_ctx = RequestContext({"user": current_user, "csrf_token": token})
            
            # Build a full context including globals
            full_context = request_ctx.build_context()
            
            # Add additional variables
            request_ctx["flash_messages"] = get_flash_messages()
    """
    
    def __init__(
        self,
        initial: Optional[Dict[str, Any]] = None,
        include_globals: bool = True
    ) -> None:
        """
            Construct a request context.
            
            :param initial: Initial request-scoped variables as a dictionary.
                If None, an empty context is created.
            :param include_globals: Whether to include global context variables
                when building the full context. Defaults to True.
        """
        super().__init__(initial)
        self._include_globals = include_globals
        return
    
    def build_context(
        self,
        extra: Optional[Dict[str, Any]] = None
    ) -> TemplateContext:
        """
            Build a full template context by merging global and request-scoped variables.
            
            The merge order is:
            1. Global context variables (lowest priority)
            2. Request-scoped variables (this context)
            3. Extra variables (highest priority)
            
            :param extra: Additional variables to merge with highest priority.
            
            :returns: A new TemplateContext containing all merged variables.
        """
        merged_data: Dict[str, Any] = {}
        
        if self._include_globals:
            merged_data.update(GlobalContext.to_dict())
        
        merged_data.update(self._data)
        
        if extra is not None:
            merged_data.update(extra)
        
        return TemplateContext(merged_data)


class ContextProcessorRegistry:
    """
        Registry for context processor functions.
        
        Context processors are functions that receive a context dictionary
        and return additional variables to merge into the template context.
        They are invoked before every template render to inject common
        variables such as request data, configuration values, or utility
        functions.
        
        A context processor is a callable with the signature::
        
            def my_processor(context: Dict[str, Any]) -> Dict[str, Any]:
                return {"extra_var": "value"}
        
        Example usage::
        
            registry = ContextProcessorRegistry()
            
            # Register a processor
            registry.register(lambda ctx: {"year": 2024})
            
            # Process a context
            extra_vars = registry.process({"title": "Home"})
            # extra_vars == {"year": 2024}
    """
    
    def __init__(self) -> None:
        """
            Construct a context processor registry.
        """
        self._processors: List[Callable[[Dict[str, Any]], Dict[str, Any]]] = []
        return
    
    def register(
        self,
        processor: Callable[[Dict[str, Any]], Dict[str, Any]]
    ) -> None:
        """
            Register a context processor function.
            
            :param processor: A callable that receives a context dictionary
                and returns a dictionary of additional variables.
        """
        self._processors.append(processor)
        return
    
    def unregister(
        self,
        processor: Callable[[Dict[str, Any]], Dict[str, Any]]
    ) -> None:
        """
            Unregister a context processor function.
            
            :param processor: The processor function to remove.
            
            :raises ValueError: If the processor is not registered.
        """
        self._processors.remove(processor)
        return
    
    def process(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
            Run all registered context processors and collect their results.
            
            Each processor receives the current context dictionary and returns
            a dictionary of additional variables. The results from all processors
            are merged together, with later processors taking precedence over
            earlier ones when keys conflict.
            
            :param context: The current context dictionary to pass to processors.
            
            :returns: A dictionary containing all additional variables from
                all registered processors.
        """
        result: Dict[str, Any] = {}
        
        for processor in self._processors:
            additional = processor(context)
            if additional is not None:
                result.update(additional)
        
        return result
    
    def clear(self) -> None:
        """
            Remove all registered context processors.
        """
        self._processors.clear()
        return
    
    @property
    def count(self) -> int:
        """
            Return the number of registered context processors.
            
            :returns: The count of registered processors.
        """
        return len(self._processors)
