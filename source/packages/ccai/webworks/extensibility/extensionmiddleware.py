"""
    Extension middleware adapter for the extensibility system.

    This module defines the ExtensionMiddleware class, which puts a
    middleware component an extension registers through the
    ``register_middleware`` hook on the application's request pipeline.
"""

import asyncio
import concurrent.futures
import inspect
import logging

from typing import Any, Awaitable, Callable

from ccai.webworks.extensibility.componenthooks import REGISTER_MIDDLEWARE


logger = logging.getLogger("ccai.webworks.extensibility.extensionmiddleware")


#: Priority of an extension middleware that does not declare one, the
#: pipeline's default.
DEFAULT_EXTENSION_MIDDLEWARE_PRIORITY = 50

#: Position of an extension middleware that does not declare one.
DEFAULT_EXTENSION_MIDDLEWARE_POSITION = "end"


def _call_maybe_async_blocking(method: Callable, *args: Any) -> Any:
    """
        Call a component method from synchronous code, driving it to
        completion when it is a coroutine function.

        When the calling thread has no running event loop the coroutine runs
        on a new loop here. When it has one, blocking on that loop would
        deadlock it, so the coroutine runs on a new loop in a helper thread.

        :param method: The component method.
        :param args: The arguments to call it with.

        :returns: What the method returned.
    """
    result = method(*args)

    if inspect.isawaitable(result):
        async def drive() -> Any:
            return await result

        try:
            asyncio.get_running_loop()
            loop_is_running = True
        except RuntimeError:
            loop_is_running = False

        if loop_is_running:
            with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
                future = pool.submit(asyncio.run, drive())
                result = future.result()
        else:
            result = asyncio.run(drive())

    return result


async def _call_maybe_async(method: Callable, *args: Any) -> Any:
    """
        Call a component method from the async pipeline.

        A coroutine function is awaited on the event loop. A plain method
        may block, so it runs on a worker thread, as the dispatcher runs
        synchronous handlers.

        :param method: The component method.
        :param args: The arguments to call it with.

        :returns: What the method returned.
    """
    if inspect.iscoroutinefunction(method):
        result = await method(*args)
    else:
        result = await asyncio.to_thread(method, *args)
        if inspect.isawaitable(result):
            result = await result

    return result


class ExtensionMiddleware:
    """
        Adapts a middleware component registered through the
        ``register_middleware`` hook to the request pipeline's middleware
        contract, ``middleware(request, call_next) -> response``.

        The extensibility specification describes such a component by two
        methods, which :class:`ComponentValidator` checks for:

        * ``process_request(request)`` -- runs before the rest of the
          pipeline. Returning None lets the request continue; returning a
          response short-circuits it: ``call_next`` is not called and that
          response is the one this middleware returns.
        * ``process_response(request, response)`` -- runs with every response
          this middleware returns (from ``call_next`` or from
          ``process_request``). Returning a response replaces it; returning
          None keeps it (it may have been changed in place).

        Either method may be a coroutine function. In the asynchronous
        pipeline (ASGI) a plain method runs on a worker thread, so a
        blocking component does not stall the event loop; in the
        synchronous pipeline a coroutine method is driven to completion.

        Optional attributes of the component place it in the pipeline:
        ``name`` (default: the component's class name), ``priority``
        (default 50, lower runs first) and ``position`` (``"start"``,
        ``"end"`` (default), ``"before:<name>"`` or ``"after:<name>"``).

        :param component: The middleware component.
    """

    def __init__(self, component: Any):
        self._component = component

        name = getattr(component, "name", None)
        if not isinstance(name, str) or name == "":
            name = type(component).__name__
        self.name: str = name

        priority = getattr(component, "priority", DEFAULT_EXTENSION_MIDDLEWARE_PRIORITY)
        if not isinstance(priority, int) or isinstance(priority, bool):
            errmsg = "The 'priority' of middleware component {!r} must be an integer, got {!r}".format(
                component, priority
            )
            raise TypeError(errmsg)
        self._priority: int = priority

        position = getattr(component, "position", DEFAULT_EXTENSION_MIDDLEWARE_POSITION)
        if not isinstance(position, str):
            errmsg = "The 'position' of middleware component {!r} must be a string, got {!r}".format(
                component, position
            )
            raise TypeError(errmsg)
        self._position: str = position

        return

    @property
    def component(self) -> Any:
        """
            The adapted middleware component.

            :returns: The component.
        """
        rtnval = self._component
        return rtnval

    @property
    def priority(self) -> int:
        """
            The pipeline priority of the component.

            :returns: The priority (lower runs first).
        """
        rtnval = self._priority
        return rtnval

    @property
    def position(self) -> str:
        """
            The pipeline position of the component.

            :returns: The positional hint.
        """
        rtnval = self._position
        return rtnval

    def __call__(self, request: Any, call_next: Callable[[Any], Any]) -> Any:
        """
            Run the component in the synchronous pipeline.

            :param request: The incoming request.
            :param call_next: The rest of the pipeline.

            :returns: The response.
        """
        response = _call_maybe_async_blocking(self._component.process_request, request)

        if response is None:
            response = call_next(request)

        replacement = _call_maybe_async_blocking(self._component.process_response, request, response)
        if replacement is not None:
            response = replacement

        return response

    async def call_async(self, request: Any, call_next: Callable[[Any], Awaitable[Any]]) -> Any:
        """
            Run the component in the asynchronous pipeline.

            :param request: The incoming request.
            :param call_next: The rest of the pipeline.

            :returns: The response.
        """
        response = await _call_maybe_async(self._component.process_request, request)

        if response is None:
            response = await call_next(request)

        replacement = await _call_maybe_async(self._component.process_response, request, response)
        if replacement is not None:
            response = replacement

        return response

    def __repr__(self) -> str:
        """
            Get string representation.

            :returns: String representation.
        """
        rtnval = "ExtensionMiddleware(name={!r}, priority={}, position={!r})".format(
            self.name, self._priority, self._position
        )
        return rtnval


def register_extension_middleware(middleware_registry: Any, component: Any) -> ExtensionMiddleware:
    """
        Put a middleware component registered through the
        ``register_middleware`` hook on an application's pipeline: adapt it
        with :class:`ExtensionMiddleware`, register the adapter as global
        middleware with the component's priority and position, and record
        the component as an extension component of the registry.

        :param middleware_registry: The application's MiddlewareRegistry.
        :param component: The middleware component.

        :returns: The adapter registered on the pipeline.

        :raises TypeError: If the component's priority or position has the
            wrong type.
        :raises ValueError: If its position names middleware that is not
            registered.
    """
    adapter = ExtensionMiddleware(component)

    middleware_registry.register(
        adapter,
        name=adapter.name,
        scope="global",
        priority=adapter.priority,
        position=adapter.position
    )
    middleware_registry.register_extension_component(REGISTER_MIDDLEWARE, component)

    logger.debug("Registered extension middleware %r on the global pipeline", adapter)

    return adapter
