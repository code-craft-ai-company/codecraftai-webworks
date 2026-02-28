"""
    Application lifecycle hooks for the extensibility system.

    This module defines the hook name constants and the AppLifecycleHooks
    class that wraps the HookManager to provide application lifecycle hook
    execution for the web framework. The hooks allow extensions to inject
    custom processing at various stages of the application lifecycle such
    as initialization, configuration loading, route registration, readiness,
    and shutdown.
"""

import logging

from typing import Any, List

from automojo.webworks.extensibility.hookmanager import HookManager


logger = logging.getLogger("automojo.webworks.extensibility.applifecyclehooks")


# =============================================================================
# Application Lifecycle Hook Name Constants
# =============================================================================

ON_APP_INIT = "on_app_init"
"""Hook called during application initialization."""

ON_APP_READY = "on_app_ready"
"""Hook called when the application is ready to serve requests."""

ON_APP_SHUTDOWN = "on_app_shutdown"
"""Hook called during application shutdown."""

ON_CONFIG_LOADED = "on_config_loaded"
"""Hook called after configuration is loaded."""

ON_ROUTES_REGISTERED = "on_routes_registered"
"""Hook called after all routes are registered."""


APP_LIFECYCLE_HOOKS = [
    ON_APP_INIT,
    ON_APP_READY,
    ON_APP_SHUTDOWN,
    ON_CONFIG_LOADED,
    ON_ROUTES_REGISTERED,
]
"""List of all application lifecycle hook names."""



class AppLifecycleHooks:
    """
        Wraps a HookManager to provide application lifecycle hook execution.

        This class manages the firing of application lifecycle hooks at the
        appropriate points during the application lifecycle. Each fire method
        delegates to the HookManager.execute() method which already handles
        error isolation by catching exceptions from individual callbacks and
        continuing with the remaining callbacks.

        :param hook_manager: The HookManager instance to use for hook execution.
    """

    def __init__(self, hook_manager: HookManager):
        self._hook_manager = hook_manager
        return

    @property
    def hook_manager(self) -> HookManager:
        """
            Get the underlying HookManager instance.

            :returns: The HookManager used by this instance.
        """
        return self._hook_manager

    def fire_on_app_init(self, *args: Any, **kwargs: Any) -> List[Any]:
        """
            Fire the on_app_init hook during application initialization.

            This hook is called during the application initialization phase,
            allowing extensions to perform setup logic. Errors in individual
            callbacks are caught and logged by the HookManager so that one
            failing hook does not prevent other hooks from executing.

            :param args: Positional arguments to pass to hook callbacks.
            :param kwargs: Keyword arguments to pass to hook callbacks.

            :returns: A list of return values from the hook callbacks.
        """
        results = self._hook_manager.execute(ON_APP_INIT, *args, **kwargs)

        return results

    def fire_on_app_ready(self, *args: Any, **kwargs: Any) -> List[Any]:
        """
            Fire the on_app_ready hook when the application is ready to serve.

            This hook is called after all initialization is complete and the
            application is ready to accept requests.

            :param args: Positional arguments to pass to hook callbacks.
            :param kwargs: Keyword arguments to pass to hook callbacks.

            :returns: A list of return values from the hook callbacks.
        """
        results = self._hook_manager.execute(ON_APP_READY, *args, **kwargs)

        return results

    def fire_on_app_shutdown(self, *args: Any, **kwargs: Any) -> List[Any]:
        """
            Fire the on_app_shutdown hook during application shutdown.

            This hook is called when the application is shutting down,
            allowing extensions to perform cleanup operations.

            :param args: Positional arguments to pass to hook callbacks.
            :param kwargs: Keyword arguments to pass to hook callbacks.

            :returns: A list of return values from the hook callbacks.
        """
        results = self._hook_manager.execute(ON_APP_SHUTDOWN, *args, **kwargs)

        return results

    def fire_on_config_loaded(self, *args: Any, **kwargs: Any) -> List[Any]:
        """
            Fire the on_config_loaded hook after configuration is loaded.

            This hook is called after the application configuration has been
            loaded, allowing extensions to react to configuration changes or
            perform configuration-dependent setup.

            :param args: Positional arguments to pass to hook callbacks.
            :param kwargs: Keyword arguments to pass to hook callbacks.

            :returns: A list of return values from the hook callbacks.
        """
        results = self._hook_manager.execute(ON_CONFIG_LOADED, *args, **kwargs)

        return results

    def fire_on_routes_registered(self, *args: Any, **kwargs: Any) -> List[Any]:
        """
            Fire the on_routes_registered hook after all routes are registered.

            This hook is called after all routes have been registered with the
            application, allowing extensions to inspect or modify the routing
            configuration.

            :param args: Positional arguments to pass to hook callbacks.
            :param kwargs: Keyword arguments to pass to hook callbacks.

            :returns: A list of return values from the hook callbacks.
        """
        results = self._hook_manager.execute(ON_ROUTES_REGISTERED, *args, **kwargs)

        return results
