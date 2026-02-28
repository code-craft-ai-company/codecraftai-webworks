"""
    Middleware module.
    
    This module provides the Middleware and AsyncMiddleware protocols for
    composable request processing, along with the MiddlewarePipeline class
    for managing ordered middleware chains.
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
        
        Stores the middleware callable along with its optional name for
        reference during positional operations.
    """
    
    def __init__(
        self,
        middleware: Union[Middleware, Callable[[Request, Callable[[Request], Response]], Response]],
        name: Optional[str] = None
    ):
        """
            Construct a MiddlewareEntry.
            
            :param middleware: The middleware callable.
            :param name: Optional name for the middleware.
        """
        self._middleware = middleware
        
        # Try to get name from middleware if not provided
        if name is None:
            name = getattr(middleware, "name", None)
        
        self._name = name
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
    
    def __repr__(self) -> str:
        """
            Get string representation.
            
            :returns: String representation.
        """
        if self._name:
            return f"MiddlewareEntry(name={self._name!r})"
        return f"MiddlewareEntry({self._middleware!r})"


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
        position: str = "end"
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
            
            :raises ValueError: If position references unknown middleware.
        """
        entry = MiddlewareEntry(middleware, name)
        
        if position == "end":
            self._entries.append(entry)
        elif position == "start":
            self._entries.insert(0, entry)
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
