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

import asyncio
import contextvars
import inspect
import threading

from typing import (
    Any,
    Awaitable,
    Callable,
    Dict,
    Iterable,
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
    
    @property
    def headers(self) -> Dict[str, str]:
        """Response headers."""
    
    @property
    def body(self) -> bytes:
        """Response body."""


# Import Request for type hints
from ccai.webworks.routing.request import Request


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


#: Name of the optional method a middleware object provides when it has an
#: asynchronous form alongside its synchronous ``__call__``. The async
#: pipeline calls it in preference to bridging ``__call__`` through a thread.
ASYNC_CALL_METHOD_NAME = "call_async"


def _get_async_callable(middleware: Any) -> Optional[Callable]:
    """
        Get the callable the async pipeline awaits for a middleware, if the
        middleware has one.

        A middleware is asynchronous when it is a coroutine function, when
        it is an object whose ``__call__`` is a coroutine function (the
        :class:`AsyncMiddleware` protocol), or when it provides a
        ``call_async`` coroutine method next to a synchronous ``__call__``.

        :param middleware: The middleware to inspect.

        :returns: The coroutine function to await, or None when the
                  middleware only has a synchronous form.
    """
    rtnval: Optional[Callable] = None

    call_async = getattr(middleware, ASYNC_CALL_METHOD_NAME, None)

    if call_async is not None and inspect.iscoroutinefunction(call_async):
        rtnval = call_async
    elif inspect.iscoroutinefunction(middleware):
        rtnval = middleware
    elif not inspect.isfunction(middleware) and not inspect.ismethod(middleware):
        call_method = getattr(middleware, "__call__", None)
        if call_method is not None and inspect.iscoroutinefunction(call_method):
            rtnval = middleware

    return rtnval


async def _call_sync_middleware(
    middleware: Callable,
    request: Request,
    next_fn: Callable[[Request], Awaitable[Response]]
) -> Any:
    """
        Run a synchronous middleware from the async pipeline.

        A synchronous middleware blocks while it waits for ``call_next``,
        and the rest of the chain is asynchronous, so it can not run on the
        event loop: the loop would be waiting on itself. The middleware
        runs on a thread of its own instead. When it calls ``call_next``
        that thread hands the downstream chain back to the event loop and
        waits for the response.

        A thread is started per call rather than borrowed from the default
        executor. A bridged middleware holds its thread until everything
        downstream has finished; drawing those threads from the pool that
        also runs offloaded handlers would let waiting middleware exhaust
        the pool and deadlock the handlers they are waiting for.

        :param middleware: The synchronous middleware callable.
        :param request: The incoming Request.
        :param next_fn: The async callable for the rest of the chain.

        :returns: Whatever the middleware returned.
    """
    loop = asyncio.get_running_loop()
    outcome: "asyncio.Future[Any]" = loop.create_future()

    def sync_next(next_request: Request) -> Response:
        try:
            running_loop = asyncio.get_running_loop()
        except RuntimeError:
            running_loop = None

        if running_loop is loop:
            raise RuntimeError(
                "A synchronous middleware called call_next on the event loop thread. "
                "call_next of a synchronous middleware must be called from the "
                "middleware's own call."
            )

        future = asyncio.run_coroutine_threadsafe(next_fn(next_request), loop)
        return future.result()

    def deliver(result: Any, error: Optional[BaseException]) -> None:
        if outcome.cancelled():
            return
        if error is not None:
            outcome.set_exception(error)
        else:
            outcome.set_result(result)
        return

    context = contextvars.copy_context()

    def run() -> None:
        result = None
        error: Optional[BaseException] = None

        try:
            result = context.run(middleware, request, sync_next)
        except BaseException as exc:
            error = exc

        try:
            loop.call_soon_threadsafe(deliver, result, error)
        except RuntimeError:
            # The event loop was closed while the middleware was
            # running; nobody is waiting for the outcome any more.
            pass

        return

    worker = threading.Thread(target=run, name="webworks-sync-middleware", daemon=True)
    worker.start()

    rtnval = await outcome

    return rtnval


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
    
    def extend(self, entries: Iterable[MiddlewareEntry]) -> None:
        """
            Append middleware entries in the order given.

            Unlike :meth:`add`, the entries are not placed by priority:
            their order was decided where they were registered, and
            appending keeps it. Used to compose a pipeline from lists that
            are already ordered, such as the scopes of a
            :class:`MiddlewareRegistry`.

            :param entries: MiddlewareEntry objects to append; another
                MiddlewarePipeline may be passed.
        """
        for entry in entries:
            self._entries.append(entry)
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

            Each middleware runs in the form it provides:

            - a coroutine function, an object with an ``async __call__`` or
              an object with a ``call_async`` coroutine method is awaited
              on the event loop with the async ``call_next``;
            - a synchronous middleware runs on its own thread, where its
              ``call_next`` blocks until the event loop has produced the
              downstream response.
            
            :param request: The incoming Request.
            :param handler: The async endpoint handler to wrap.
            
            :returns: Response from the pipeline.
        """
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
                async_callable = _get_async_callable(mw)

                async def async_wrapper(req: Request) -> Response:
                    if async_callable is not None:
                        result = await async_callable(req, next_fn)
                    else:
                        result = await _call_sync_middleware(mw, req, next_fn)

                    # A middleware may hand back the awaitable it received
                    # from call_next instead of awaiting it.
                    if inspect.isawaitable(result):
                        result = await result

                    return result
                
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
        factory_registry: Optional[Dict[str, Callable]] = None,
        allow_placeholders: bool = False
    ) -> "MiddlewarePipeline":
        """
            Reconstruct a pipeline from a list of middleware configuration
            dictionaries.

            Each dictionary in the config list should contain at minimum a
            'name' key. Optional keys include 'priority' (default 50) and
            'scope' (default "global").

            A factory_registry mapping middleware names to factory callables
            is required to instantiate the actual middleware objects. A name
            that is not in the factory_registry is an error: a pipeline that
            lists a middleware it does not run -- a mistyped name, an
            ``authentication`` or ``csrf`` entry whose factory was never
            registered -- would report a protection that is not there.

            :param config: List of middleware configuration dictionaries.
            :param factory_registry: Optional mapping of middleware names to
                factory callables that produce middleware instances.
            :param allow_placeholders: If True, an entry without a factory
                becomes a pass-through placeholder carrying the entry's
                name instead of raising. Intended for tooling that only
                inspects the shape of a pipeline; a placeholder does no
                work when a request passes through it.

            :returns: A reconstructed MiddlewarePipeline.

            :raises ValueError: If an entry names a middleware that has no
                factory and ``allow_placeholders`` is False.
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
            elif allow_placeholders is True:
                # Create a passthrough placeholder middleware
                def _make_passthrough(n: Optional[str]) -> Callable:
                    def passthrough(request: Request, call_next: Callable) -> Any:
                        return call_next(request)
                    passthrough.name = n  # type: ignore[attr-defined]
                    return passthrough
                middleware = _make_passthrough(mw_name)
            else:
                known_names = ", ".join(sorted(factory_registry.keys()))
                raise ValueError(
                    f"No middleware factory is registered for {mw_name!r}; "
                    f"the pipeline can not be built without it. "
                    f"Registered factories: [{known_names}]"
                )

            pipeline.add(
                middleware,
                name=mw_name,
                priority=mw_priority,
                scope=mw_scope,
            )

        return pipeline
