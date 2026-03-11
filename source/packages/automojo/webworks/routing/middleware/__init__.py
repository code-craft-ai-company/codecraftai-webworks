"""
    Middleware module.
    
    This module provides the Middleware and AsyncMiddleware protocols for
    composable request processing, along with the MiddlewarePipeline class
    for managing ordered middleware chains.

    Built-in middleware components are available in submodules:
    - ``cors``: CORSMiddleware for Cross-Origin Resource Sharing
    - ``logging``: RequestLoggingMiddleware for request/response logging
    - ``errornormalization``: ErrorNormalizationMiddleware for error handling
"""

from typing import (
    Any,
    Awaitable,
    Callable,
    Dict,
    List,
    Optional,
    Protocol,
    Tuple,
    Union,
    runtime_checkable,
)


# Forward reference for Response type
# The actual Response class will be imported at runtime when needed
class Response(Protocol):
    """
        Protocol for Response objects.
        
        This protocol defines the minimal interface expected from Response
        objects used in middleware processing.
    """
    
    @property
    def status_code(self) -> int:
        """HTTP status code."""
        ...
    
    @property
    def headers(self) -> Dict[str, str]:
        """Response headers."""
        ...
    
    @property
    def body(self) -> bytes:
        """Response body."""
        ...


# Import Request for type hints
from automojo.webworks.routing.request import Request


@runtime_checkable
class Middleware(Protocol):
    """
        Protocol for middleware components that wrap request handling.
        
        Middleware components receive a request and a call_next callable,
        allowing them to:
        - Modify the request before passing it to the next handler
        - Modify the response after receiving it from the next handler
        - Short-circuit the pipeline by returning a response without calling call_next
        
        The optional name attribute allows middleware to be referenced for
        positional insertion and removal in the pipeline.
    """
    
    name: str  # Optional name for positional insertion/removal
    
    def __call__(
        self,
        request: Request,
        call_next: Callable[[Request], Response]
    ) -> Response:
        """
            Process a request, optionally calling the next handler.
            
            :param request: The incoming Request.
            :param call_next: Callable to invoke next middleware/handler.
            
            :returns: Response from handler or short-circuit response.
        """
        ...


@runtime_checkable
class AsyncMiddleware(Protocol):
    """
        Protocol for async middleware components.
        
        Similar to Middleware but supports async/await for non-blocking
        request processing.
    """
    
    name: str  # Optional name for positional insertion/removal
    
    async def __call__(
        self,
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        """
            Process a request asynchronously, optionally calling the next handler.
            
            :param request: The incoming Request.
            :param call_next: Async callable to invoke next middleware/handler.
            
            :returns: Response from handler or short-circuit response.
        """
        ...


class MiddlewareEntry:
    """
        Internal class representing a middleware entry in the pipeline.

        Stores the middleware callable along with its optional name,
        priority, and scope metadata for reference during positional
        operations and pipeline composition.
    """

    def __init__(
        self,
        middleware: Union[Middleware, Callable[[Request, Callable[[Request], Response]], Response]],
        name: Optional[str] = None,
        priority: int = 50,
        scope: str = "global"
    ):
        """
            Construct a MiddlewareEntry.

            :param middleware: The middleware callable.
            :param name: Optional name for the middleware.
            :param priority: Numeric priority for ordering within the same
                positional group. Lower values execute first. Default is 50.
            :param scope: The scope at which this middleware is applied.
                One of "global", "blueprint", or "route". Default is "global".
        """
        self._middleware = middleware

        # Try to get name from middleware if not provided
        if name is None:
            name = getattr(middleware, "name", None)

        self._name = name
        self._priority = priority
        self._scope = scope
        return

    @property
    def middleware(self) -> Union[Middleware, Callable[[Request, Callable[[Request], Response]], Response]]:
        """
            Get the middleware callable.

            :returns: The middleware callable.
        """
        return self._middleware

    @property
    def name(self) -> Optional[str]:
        """
            Get the middleware name.

            :returns: The middleware name or None.
        """
        return self._name

    @property
    def priority(self) -> int:
        """
            Get the middleware priority.

            Lower values execute first within the same positional group.

            :returns: The numeric priority value.
        """
        return self._priority

    @property
    def scope(self) -> str:
        """
            Get the middleware scope.

            :returns: The scope string ("global", "blueprint", or "route").
        """
        return self._scope

    def as_dict(self) -> Dict[str, Any]:
        """
            Return a dictionary representation of this entry.

            :returns: Dictionary with keys 'name', 'priority', and 'scope'.
        """
        return {
            "name": self._name,
            "priority": self._priority,
            "scope": self._scope,
        }

    def __repr__(self) -> str:
        """
            Get string representation.

            :returns: String representation.
        """
        if self._name:
            return f"MiddlewareEntry(name={self._name!r}, priority={self._priority}, scope={self._scope!r})"
        return f"MiddlewareEntry({self._middleware!r}, priority={self._priority}, scope={self._scope!r})"


import inspect


def _validate_middleware(middleware: Any) -> None:
    """
        Validate that a middleware conforms to the Middleware or AsyncMiddleware
        protocol, or is a plain callable with the correct signature.
        
        Middleware is considered valid if it:
        - Is an instance of the Middleware protocol (has name and __call__ with correct sig)
        - Is an instance of the AsyncMiddleware protocol (has name and async __call__)
        - Is a plain callable accepting (request, call_next) parameters
        
        :param middleware: The middleware to validate.
        
        :raises TypeError: If middleware does not conform to any accepted pattern.
    """
    # Check if it conforms to the Middleware or AsyncMiddleware protocol
    if isinstance(middleware, (Middleware, AsyncMiddleware)):
        return
    
    # Check if it is a plain callable with the right signature
    if callable(middleware):
        try:
            sig = inspect.signature(middleware)
            params = [
                p for p in sig.parameters.values()
                if p.default is inspect.Parameter.empty
                and p.kind in (
                    inspect.Parameter.POSITIONAL_ONLY,
                    inspect.Parameter.POSITIONAL_OR_KEYWORD,
                )
            ]
            # Must accept at least 2 positional parameters (request, call_next)
            if len(params) >= 2:
                return
        except (ValueError, TypeError):
            # If we cannot inspect the signature, accept it as a callable
            return
    
    raise TypeError(
        f"Middleware {middleware!r} does not conform to the Middleware or "
        f"AsyncMiddleware protocol and is not a callable with "
        f"(request, call_next) signature. Middleware must either implement "
        f"the Middleware/AsyncMiddleware protocol (with a 'name' attribute "
        f"and a '__call__' method) or be a callable accepting (request, call_next)."
    )


class MiddlewarePipeline:
    """
        Ordered chain of middleware components that process requests
        before and after the endpoint handler.
        
        The pipeline executes middleware in order, with each middleware
        wrapping the next. This creates a nested call structure where:
        - Request flows forward through middleware (MW1 -> MW2 -> ... -> Handler)
        - Response flows backward through middleware (Handler -> ... -> MW2 -> MW1)
        
        Middleware can:
        - Modify requests before passing to the next handler
        - Modify responses after receiving from the next handler
        - Short-circuit by returning a response without calling call_next
    """
    
    def __init__(self):
        """
            Construct an empty middleware pipeline.
        """
        self._entries: List[MiddlewareEntry] = []
        return
    
    
    def add(
        self,
        middleware: Union[Middleware, Callable[[Request, Callable[[Request], Response]], Response]],
        name: Optional[str] = None,
        position: str = "end",
        priority: int = 50,
        scope: str = "global"
    ) -> None:
        """
            Add middleware to the pipeline.
            
            :param middleware: Middleware component to add.
            :param name: Optional name for later reference.
            :param position: Where to insert:
                - "start": Beginning of pipeline
                - "end": End of pipeline (default)
                - "before:<name>": Before named middleware
                - "after:<name>": After named middleware
            :param priority: Numeric priority for ordering within the same
                positional group. Lower values execute first. Default is 50.
            :param scope: The scope at which this middleware is applied.
                One of "global", "blueprint", or "route". Default is "global".
            
            :raises ValueError: If position references unknown middleware.
            :raises TypeError: If middleware does not conform to the Middleware
                or AsyncMiddleware protocol and is not a valid callable.
        """
        _validate_middleware(middleware)
        
        entry = MiddlewareEntry(middleware, name, priority=priority, scope=scope)
        
        if position == "end":
            # Insert at end, but maintain priority ordering among entries
            # that were added at the end position. Find the insertion point
            # by scanning from the end to find where this entry fits by priority.
            insert_idx = len(self._entries)
            # Walk backward from the end to find the correct position
            # among entries that share the "end" group. We insert before
            # any trailing entry with a higher priority value (lower priority
            # means execute first).
            while insert_idx > 0 and self._entries[insert_idx - 1].priority > priority:
                insert_idx -= 1
            self._entries.insert(insert_idx, entry)
        elif position == "start":
            # Insert at start, maintaining priority ordering among entries
            # that were added at the start position.
            insert_idx = 0
            while insert_idx < len(self._entries) and self._entries[insert_idx].priority < priority:
                insert_idx += 1
            self._entries.insert(insert_idx, entry)
        elif position.startswith("before:"):
            target_name = position[7:]  # Remove "before:" prefix
            index = self._find_index_by_name(target_name)
            if index is None:
                raise ValueError(f"Middleware '{target_name}' not found in pipeline")
            self._entries.insert(index, entry)
        elif position.startswith("after:"):
            target_name = position[6:]  # Remove "after:" prefix
            index = self._find_index_by_name(target_name)
            if index is None:
                raise ValueError(f"Middleware '{target_name}' not found in pipeline")
            self._entries.insert(index + 1, entry)
        else:
            raise ValueError(f"Invalid position: {position}")
        
        return

    
    def remove(self, name: str) -> None:
        """
            Remove middleware by name.
            
            :param name: Name of middleware to remove.
            
            :raises KeyError: If name not found.
        """
        index = self._find_index_by_name(name)
        if index is None:
            raise KeyError(f"Middleware '{name}' not found in pipeline")
        
        del self._entries[index]
        return
    
    def _find_index_by_name(self, name: str) -> Optional[int]:
        """
            Find the index of middleware by name.
            
            :param name: Name to search for.
            
            :returns: Index if found, None otherwise.
        """
        for i, entry in enumerate(self._entries):
            if entry.name == name:
                return i
        return None
    
    def execute(
        self,
        request: Request,
        handler: Callable[[Request], Response]
    ) -> Response:
        """
            Execute the pipeline with the given handler as final callable.
            
            Middleware is executed in order, with each middleware wrapping
            the next. The handler is called as the final step.
            
            :param request: The incoming Request.
            :param handler: The endpoint handler to wrap.
            
            :returns: Response from the pipeline.
        """
        # Build the call chain from the end (handler) to the start
        # Each middleware wraps the next callable
        current_callable: Callable[[Request], Response] = handler
        
        # Iterate in reverse order to build the chain
        for entry in reversed(self._entries):
            # Capture the current callable in a closure
            next_callable = current_callable
            middleware = entry.middleware
            
            # Create a wrapper that calls this middleware with the next callable
            def make_wrapper(
                mw: Callable[[Request, Callable[[Request], Response]], Response],
                next_fn: Callable[[Request], Response]
            ) -> Callable[[Request], Response]:
                def wrapper(req: Request) -> Response:
                    return mw(req, next_fn)
                return wrapper
            
            current_callable = make_wrapper(middleware, next_callable)
        
        # Execute the chain starting from the first middleware
        response = current_callable(request)
        return response
    
    async def execute_async(
        self,
        request: Request,
        handler: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        """
            Execute the pipeline asynchronously.
            
            Similar to execute() but supports async middleware and handlers.
            
            :param request: The incoming Request.
            :param handler: The async endpoint handler to wrap.
            
            :returns: Response from the pipeline.
        """
        import asyncio
        
        # Build the async call chain from the end (handler) to the start
        current_callable: Callable[[Request], Awaitable[Response]] = handler
        
        # Iterate in reverse order to build the chain
        for entry in reversed(self._entries):
            next_callable = current_callable
            middleware = entry.middleware
            
            # Create an async wrapper
            def make_async_wrapper(
                mw: Any,
                next_fn: Callable[[Request], Awaitable[Response]]
            ) -> Callable[[Request], Awaitable[Response]]:
                async def async_wrapper(req: Request) -> Response:
                    # Check if middleware is async
                    if asyncio.iscoroutinefunction(mw):
                        return await mw(req, next_fn)
                    else:
                        # Sync middleware - wrap next_fn to be sync-compatible
                        def sync_next(r: Request) -> Response:
                            # Run the async next_fn in the event loop
                            # This is a simplification - in practice, you'd want
                            # to handle this more carefully
                            loop = asyncio.get_event_loop()
                            if loop.is_running():
                                # Create a new task and wait for it
                                import concurrent.futures
                                future = asyncio.ensure_future(next_fn(r))
                                # We need to await this, but we're in sync context
                                # This is a limitation - sync middleware in async
                                # pipeline should ideally be avoided
                                raise RuntimeError(
                                    "Sync middleware cannot call async next in running loop. "
                                    "Use async middleware for async pipelines."
                                )
                            else:
                                return loop.run_until_complete(next_fn(r))
                        
                        return mw(req, sync_next)
                
                return async_wrapper
            
            current_callable = make_async_wrapper(middleware, next_callable)
        
        # Execute the chain starting from the first middleware
        response = await current_callable(request)
        return response
    
    def __len__(self) -> int:
        """
            Get the number of middleware in the pipeline.
            
            :returns: Number of middleware entries.
        """
        return len(self._entries)
    
    def __iter__(self):
        """
            Iterate over middleware entries.
            
            :returns: Iterator over MiddlewareEntry objects.
        """
        return iter(self._entries)
    
    def get_names(self) -> List[Optional[str]]:
        """
            Get list of middleware names in order.
            
            :returns: List of middleware names (None for unnamed middleware).
        """
        return [entry.name for entry in self._entries]
    
    def __repr__(self) -> str:
        """
            Get string representation.
            
            :returns: String representation.
        """
        names = [entry.name or "<unnamed>" for entry in self._entries]
        return f"MiddlewarePipeline([{', '.join(names)}])"


    def as_dict(self) -> List[Dict[str, Any]]:
        """
            Return a list of dictionaries describing each MiddlewareEntry.

            Each dictionary contains keys 'name', 'priority', and 'scope'.

            :returns: List of entry dictionaries.
        """
        return [entry.as_dict() for entry in self._entries]

    def to_json(self) -> str:
        """
            Serialize the pipeline configuration to a JSON string.

            :returns: JSON string representation of the pipeline.
        """
        import json
        return json.dumps(self.as_dict())

    @classmethod
    def from_config(
        cls,
        config: List[Dict[str, Any]],
        factory_registry: Optional[Dict[str, Callable]] = None
    ) -> "MiddlewarePipeline":
        """
            Reconstruct a pipeline from a list of middleware configuration
            dictionaries.

            Each dictionary in the config list should contain at minimum a
            'name' key. Optional keys include 'priority' (default 50) and
            'scope' (default "global").

            A factory_registry mapping middleware names to factory callables
            is required to instantiate the actual middleware objects. If a
            name is not found in the factory_registry, a placeholder callable
            is used.

            :param config: List of middleware configuration dictionaries.
            :param factory_registry: Optional mapping of middleware names to
                factory callables that produce middleware instances.

            :returns: A reconstructed MiddlewarePipeline.
        """
        if factory_registry is None:
            factory_registry = {}

        pipeline = cls()

        for entry_config in config:
            mw_name = entry_config.get("name")
            mw_priority = entry_config.get("priority", 50)
            mw_scope = entry_config.get("scope", "global")

            if mw_name and mw_name in factory_registry:
                middleware = factory_registry[mw_name]()
            else:
                # Create a passthrough placeholder middleware
                def _make_passthrough(n: Optional[str]) -> Callable:
                    def passthrough(request: Request, call_next: Callable) -> Any:
                        return call_next(request)
                    passthrough.name = n  # type: ignore[attr-defined]
                    return passthrough
                middleware = _make_passthrough(mw_name)

            pipeline.add(
                middleware,
                name=mw_name,
                priority=mw_priority,
                scope=mw_scope,
            )

        return pipeline
