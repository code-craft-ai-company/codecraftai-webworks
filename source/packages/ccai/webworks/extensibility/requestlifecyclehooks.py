"""
    Request lifecycle hooks for the extensibility system.

    This module defines the hook name constants and the RequestLifecycleHooks
    class that wraps the HookManager to provide request lifecycle hook
    execution for the web framework. The hooks allow extensions to inject
    custom processing at various stages of request handling.
"""

import logging
import threading

from typing import Any, List, Optional

from ccai.webworks.extensibility.hookmanager import HookManager


logger = logging.getLogger("ccai.webworks.extensibility.requestlifecyclehooks")


# =============================================================================
# Request Lifecycle Hook Name Constants
# =============================================================================

BEFORE_REQUEST = "before_request"
"""Hook called before each request is processed."""

AFTER_REQUEST = "after_request"
"""Hook called after each request is processed."""

BEFORE_FIRST_REQUEST = "before_first_request"
"""Hook called once before the very first request."""

ON_REQUEST_ERROR = "on_request_error"
"""Hook called when an unhandled exception occurs during request processing."""

TEARDOWN_REQUEST = "teardown_request"
"""Hook called after the response is sent, for cleanup."""


REQUEST_LIFECYCLE_HOOKS = [
    BEFORE_REQUEST,
    AFTER_REQUEST,
    BEFORE_FIRST_REQUEST,
    ON_REQUEST_ERROR,
    TEARDOWN_REQUEST,
]
"""List of all request lifecycle hook names."""



class RequestLifecycleHooks:
    """
        Wraps a HookManager to provide request lifecycle hook execution.

        The dispatcher fires these hooks for every request, in the same
        order whether it dispatches synchronously (``dispatch``, WSGI) or
        asynchronously (``dispatch_async``, ASGI):

        1. ``before_first_request(request)`` -- once, before the first
           request is processed. Thread- and task-safe: concurrent first
           requests wait until the callbacks have finished, and the
           callbacks never run twice.
        2. ``before_request(request)`` -- a callback that returns a response
           short-circuits the request: the remaining callbacks, the
           middleware, routing and the handler are skipped and that
           response is sent (after ``after_request``).
        3. ``on_request_error(request, exception)`` -- when processing raised
           an exception nothing else handled, before the dispatcher turns
           it into the 500 response.
        4. ``after_request(request, response)`` -- each callback receives the
           response the previous one left; returning a response replaces
           it, returning None keeps it (it may have been changed in place).
        5. ``teardown_request(request, response, exception)`` -- always, last,
           with the response that is sent and the exception that ended the
           request (or None).

        Hook callbacks are synchronous and run on the thread that
        dispatches the request -- the event loop thread under ASGI -- so
        they must not block.

        A callback that raises is reported through the HookManager's error
        callback (logged with its extension's name, counted against the
        extension). ``before_first_request``, ``before_request`` and
        ``after_request`` decide what the request does next, so a failure
        there also ends the request: :class:`HookExecutionError` is raised
        and the dispatcher answers 500. A failing ``on_request_error`` or
        ``teardown_request`` callback is only reported: the response has
        been decided by then. ``ConfigurationError`` and ``SemanticError``
        are never caught.

        :param hook_manager: The HookManager instance to use for hook execution.
    """

    def __init__(self, hook_manager: HookManager):
        self._hook_manager = hook_manager
        self._first_request_handled = False
        self._first_request_lock = threading.Lock()
        return

    @property
    def hook_manager(self) -> HookManager:
        """
            Get the underlying HookManager instance.

            :returns: The HookManager used by this instance.
        """
        return self._hook_manager

    @property
    def first_request_handled(self) -> bool:
        """
            Check whether the first request has been handled.

            :returns: True if the first request has already been processed.
        """
        return self._first_request_handled

    def has_callbacks(self) -> bool:
        """
            Check whether any request lifecycle hook has a callback.

            The dispatcher asks this for every request and takes its plain
            path when the answer is False, so an application without
            extensions pays a dictionary-size check and nothing else.

            :returns: True if a callback is registered for any of the
                      request lifecycle hooks.
        """
        rtnval = self._hook_manager.has_any_callbacks(REQUEST_LIFECYCLE_HOOKS)
        return rtnval

    def fire_before_first_request(self, *args: Any, **kwargs: Any) -> None:
        """
            Fire the before_first_request hook if the first request has
            not yet been handled. This method is idempotent; subsequent
            calls after the first request do nothing.

            Concurrent callers are serialised: the first one runs the
            callbacks, the others wait until it has finished and then
            return without running them. The first request counts as handled
            even when a callback failed, so the callbacks run once.

            :param args: Positional arguments to pass to hook callbacks
                (the dispatcher passes the request).
            :param kwargs: Keyword arguments to pass to hook callbacks.

            :raises HookExecutionError: If a callback raised.
        """
        if self._first_request_handled is True:
            return

        with self._first_request_lock:
            if self._first_request_handled is True:
                return

            try:
                self._hook_manager.execute(BEFORE_FIRST_REQUEST, *args, stop_on_error=True, **kwargs)
            finally:
                self._first_request_handled = True

        return

    def fire_before_request(self, *args: Any, **kwargs: Any) -> Optional[Any]:
        """
            Fire the before_request hook. If any callback returns a non-None
            value, request processing is short-circuited and that value is
            returned as the response. Remaining callbacks are not executed.

            :param args: Positional arguments to pass to hook callbacks
                (the dispatcher passes the request).
            :param kwargs: Keyword arguments to pass to hook callbacks.

            :returns: The short-circuit response if a callback returned one,
                or None if all callbacks returned None.

            :raises HookExecutionError: If a callback raised.
        """
        results = self._hook_manager.execute(
            BEFORE_REQUEST, *args, stop_on_result=True, stop_on_error=True, **kwargs
        )

        for result in results:
            if result is not None:
                return result

        return None

    def fire_after_request(self, request: Any, response: Any) -> Any:
        """
            Fire the after_request hook after request processing completes.

            Each callback is called with ``(request, response)``, where
            ``response`` is the response the previous callback left. A
            callback that returns a response replaces it; one that returns
            None keeps it.

            :param request: The request that was processed.
            :param response: The response produced for it.

            :returns: The response to send.

            :raises HookExecutionError: If a callback raised.
        """
        rtnval = self._hook_manager.execute_chain(
            AFTER_REQUEST, response, request, stop_on_error=True
        )

        return rtnval

    def fire_on_request_error(self, *args: Any, **kwargs: Any) -> List[Any]:
        """
            Fire the on_request_error hook when an unhandled exception
            occurs during request processing.

            A failing callback is reported and the others still run.

            :param args: Positional arguments to pass to hook callbacks
                (the dispatcher passes the request and the exception).
            :param kwargs: Keyword arguments to pass to hook callbacks.

            :returns: A list of return values from the hook callbacks.
        """
        results = self._hook_manager.execute(ON_REQUEST_ERROR, *args, **kwargs)

        return results

    def fire_teardown_request(self, *args: Any, **kwargs: Any) -> List[Any]:
        """
            Fire the teardown_request hook after the response has been sent.
            This hook is intended for cleanup operations.

            A failing callback is reported and the others still run.

            :param args: Positional arguments to pass to hook callbacks
                (the dispatcher passes the request, the response and the
                exception that ended the request, or None).
            :param kwargs: Keyword arguments to pass to hook callbacks.

            :returns: A list of return values from the hook callbacks.
        """
        results = self._hook_manager.execute(TEARDOWN_REQUEST, *args, **kwargs)

        return results
