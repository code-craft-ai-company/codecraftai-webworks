"""
    Request lifecycle hooks for the extensibility system.

    This module defines the hook name constants and the RequestLifecycleHooks
    class that wraps the HookManager to provide request lifecycle hook
    execution for the web framework. The hooks allow extensions to inject
    custom processing at various stages of request handling.
"""

import logging

from typing import Any, List, Optional

from automojo.webworks.extensibility.hookmanager import HookManager


logger = logging.getLogger("automojo.webworks.extensibility.requestlifecyclehooks")


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

        This class manages the firing of request lifecycle hooks at the
        appropriate points during request processing. It tracks whether
        the first request has been handled and supports short-circuiting
        for before_request hooks.

        :param hook_manager: The HookManager instance to use for hook execution.
    """

    def __init__(self, hook_manager: HookManager):
        self._hook_manager = hook_manager
        self._first_request_handled = False
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

    def fire_before_first_request(self, *args: Any, **kwargs: Any) -> None:
        """
            Fire the before_first_request hook if the first request has
            not yet been handled. This method is idempotent; subsequent
            calls after the first request do nothing.

            :param args: Positional arguments to pass to hook callbacks.
            :param kwargs: Keyword arguments to pass to hook callbacks.
        """
        if self._first_request_handled is True:
            return

        self._first_request_handled = True

        self._hook_manager.execute(BEFORE_FIRST_REQUEST, *args, **kwargs)

        return

    def fire_before_request(self, *args: Any, **kwargs: Any) -> Optional[Any]:
        """
            Fire the before_request hook. If any callback returns a non-None
            value, request processing is short-circuited and that value is
            returned as the response. Remaining callbacks are not executed.

            :param args: Positional arguments to pass to hook callbacks.
            :param kwargs: Keyword arguments to pass to hook callbacks.

            :returns: The short-circuit response if a callback returned one,
                or None if all callbacks returned None.
        """
        results = self._hook_manager.execute(
            BEFORE_REQUEST, *args, stop_on_result=True, **kwargs
        )

        for result in results:
            if result is not None:
                return result

        return None

    def fire_after_request(self, *args: Any, **kwargs: Any) -> List[Any]:
        """
            Fire the after_request hook after request processing completes.

            :param args: Positional arguments to pass to hook callbacks.
            :param kwargs: Keyword arguments to pass to hook callbacks.

            :returns: A list of return values from the hook callbacks.
        """
        results = self._hook_manager.execute(AFTER_REQUEST, *args, **kwargs)

        return results

    def fire_on_request_error(self, *args: Any, **kwargs: Any) -> List[Any]:
        """
            Fire the on_request_error hook when an unhandled exception
            occurs during request processing.

            :param args: Positional arguments to pass to hook callbacks.
            :param kwargs: Keyword arguments to pass to hook callbacks.

            :returns: A list of return values from the hook callbacks.
        """
        results = self._hook_manager.execute(ON_REQUEST_ERROR, *args, **kwargs)

        return results

    def fire_teardown_request(self, *args: Any, **kwargs: Any) -> List[Any]:
        """
            Fire the teardown_request hook after the response has been sent.
            This hook is intended for cleanup operations.

            :param args: Positional arguments to pass to hook callbacks.
            :param kwargs: Keyword arguments to pass to hook callbacks.

            :returns: A list of return values from the hook callbacks.
        """
        results = self._hook_manager.execute(TEARDOWN_REQUEST, *args, **kwargs)

        return results
