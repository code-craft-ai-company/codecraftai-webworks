"""
    Application loader module for the production server.

    This module provides the ApplicationLoader class that handles
    application preloading before forking workers, application factory
    pattern support, lifecycle hooks (on_starting, on_reload, when_ready,
    on_exit), and application load error handling with proper exit codes.
"""

import importlib
import logging
import sys
from typing import Any, Callable, Dict, Optional, TYPE_CHECKING

from automojo.webworks.prodserver.serverconfig import EXIT_APP_LOAD_ERROR

if TYPE_CHECKING:
    from automojo.webworks.prodserver.serverconfig import ServerConfig


# Default logger for application loader
_logger = logging.getLogger("webworks.prodserver.applicationloader")


class ApplicationLoadError(Exception):
    """
        Raised when the application fails to load.

        Contains the original exception and a descriptive message
        suitable for logging and error reporting.
    """

    def __init__(self, message: str, original_error: Optional[Exception] = None):
        """
            Construct an ApplicationLoadError.

            :param message: Descriptive error message.
            :param original_error: The original exception that caused the load failure.
        """
        self._original_error = original_error
        super().__init__(message)
        return

    @property
    def original_error(self) -> Optional[Exception]:
        """
            Get the original exception that caused the load failure.

            :returns: The original exception, or None if not available.
        """
        return self._original_error


class ApplicationLoader:
    """
        Handles application loading, preloading, factory support,
        and lifecycle hooks for the production server.

        When preloading is enabled, the application is loaded once
        before workers are forked so that application code is shared
        across all worker processes via copy-on-write memory.

        Supports the factory pattern where an application factory
        callable is invoked to create the application instance.

        Manages lifecycle hooks that are called at specific points
        during the server lifecycle:
        - on_starting: Called before the server begins startup.
        - on_reload: Called when configuration is reloaded.
        - when_ready: Called after the server is fully started.
        - on_exit: Called when the server is shutting down.
    """

    def __init__(self, config: "ServerConfig"):
        """
            Construct an ApplicationLoader.

            :param config: Server configuration containing preload,
                           factory, and hook settings.
        """
        self._config = config
        self._app: Optional[object] = None
        self._preloaded: bool = False
        self._factory: Optional[Callable[[], object]] = None
        self._hooks: Dict[str, Optional[Callable]] = {
            "on_starting": config.on_starting,
            "on_reload": config.on_reload,
            "when_ready": config.when_ready,
            "on_exit": config.on_exit,
        }

        return

    @property
    def app(self) -> Optional[object]:
        """
            Get the loaded application instance.

            :returns: The application object, or None if not yet loaded.
        """
        return self._app

    @property
    def preloaded(self) -> bool:
        """
            Check whether the application has been preloaded.

            :returns: True if the application was preloaded before
                      worker forking.
        """
        return self._preloaded

    @property
    def factory(self) -> Optional[Callable[[], object]]:
        """
            Get the application factory callable.

            :returns: The factory callable, or None if not set.
        """
        return self._factory

    def set_factory(self, factory: Callable[[], object]) -> None:
        """
            Set the application factory callable.

            The factory is a callable that takes no arguments and
            returns an application instance. When set, the factory
            is used to create the application instead of using a
            directly provided app object.

            :param factory: A callable that returns an application instance.
        """
        self._factory = factory

        return

    def set_app(self, app: object) -> None:
        """
            Set the application instance directly.

            :param app: The application object.
        """
        self._app = app

        return

    def load_app(self, app: Optional[object] = None) -> object:
        """
            Load the application instance.

            If a factory is set, the factory is called to create the
            application. If an app object is provided directly, it is
            used as-is. If preloading is enabled, the application is
            stored for sharing across workers.

            :param app: Optional application object to use directly.

            :returns: The loaded application instance.

            :raises ApplicationLoadError: If the application fails to load.
        """
        try:
            if self._factory is not None:
                _logger.info("Loading application via factory")
                loaded_app = self._factory()
            elif app is not None:
                loaded_app = app
            elif self._app is not None:
                loaded_app = self._app
            else:
                errmsg = "No application or factory provided"
                raise ApplicationLoadError(errmsg)

            self._app = loaded_app

            _logger.info("Application loaded successfully")

        except ApplicationLoadError:
            raise
        except Exception as ex:
            errmsg = f"Failed to load application: {ex}"
            _logger.error(errmsg, exc_info=True)
            raise ApplicationLoadError(errmsg, original_error=ex)

        return loaded_app

    def preload(self, app: Optional[object] = None) -> object:
        """
            Preload the application before forking workers.

            Loads the application and marks it as preloaded so that
            worker processes can share the application code via
            copy-on-write memory. This is only performed when the
            preload configuration option is enabled.

            :param app: Optional application object to preload.

            :returns: The preloaded application instance.

            :raises ApplicationLoadError: If the application fails to load.
        """
        if not self._config.preload:
            _logger.info("Preloading disabled, skipping")
            if app is not None:
                self._app = app
            return self._app

        _logger.info("Preloading application before forking workers")

        loaded_app = self.load_app(app=app)
        self._preloaded = True

        _logger.info("Application preloaded successfully, code will be shared across workers")

        return loaded_app

    def get_app_for_worker(self) -> object:
        """
            Get the application instance for a worker process.

            If the application was preloaded, returns the shared
            application instance. If a factory is set and preloading
            is not enabled, creates a new application instance via
            the factory for each worker. Otherwise returns the
            stored application instance.

            :returns: The application instance for the worker.

            :raises ApplicationLoadError: If no application is available.
        """
        if self._preloaded and self._app is not None:
            return self._app

        if self._factory is not None and not self._preloaded:
            _logger.info("Creating application instance via factory for worker")
            try:
                worker_app = self._factory()
                return worker_app
            except Exception as ex:
                errmsg = f"Failed to create application for worker: {ex}"
                _logger.error(errmsg, exc_info=True)
                raise ApplicationLoadError(errmsg, original_error=ex) from ex

        if self._app is not None:
            return self._app

        errmsg = "No application available for worker"
        raise ApplicationLoadError(errmsg)

    def call_on_starting(self) -> None:
        """
            Call the on_starting lifecycle hook.

            The on_starting hook is called before the server begins
            its startup sequence. The hook receives the server
            configuration as its argument.

            Any exception raised by the hook is logged but does not
            prevent the server from starting.
        """
        hook = self._hooks.get("on_starting")

        if hook is None:
            return

        try:
            _logger.info("Calling on_starting hook")
            hook(self._config)
        except Exception:
            _logger.exception("Error in on_starting hook")

        return

    def call_on_reload(self) -> None:
        """
            Call the on_reload lifecycle hook.

            The on_reload hook is called when the server configuration
            is reloaded (typically via SIGHUP). The hook receives the
            server configuration as its argument.

            Any exception raised by the hook is logged but does not
            prevent the reload from continuing.
        """
        hook = self._hooks.get("on_reload")

        if hook is None:
            return

        try:
            _logger.info("Calling on_reload hook")
            hook(self._config)
        except Exception:
            _logger.exception("Error in on_reload hook")

        return

    def call_when_ready(self) -> None:
        """
            Call the when_ready lifecycle hook.

            The when_ready hook is called after the server has fully
            started and is ready to accept connections. The hook
            receives the server configuration as its argument.

            Any exception raised by the hook is logged but does not
            affect server operation.
        """
        hook = self._hooks.get("when_ready")

        if hook is None:
            return

        try:
            _logger.info("Calling when_ready hook")
            hook(self._config)
        except Exception:
            _logger.exception("Error in when_ready hook")

        return

    def call_on_exit(self) -> None:
        """
            Call the on_exit lifecycle hook.

            The on_exit hook is called when the server is shutting
            down. The hook receives the server configuration as its
            argument.

            Any exception raised by the hook is logged but does not
            prevent the shutdown from completing.
        """
        hook = self._hooks.get("on_exit")

        if hook is None:
            return

        try:
            _logger.info("Calling on_exit hook")
            hook(self._config)
        except Exception:
            _logger.exception("Error in on_exit hook")

        return

    def update_hook(self, hook_name: str, hook: Optional[Callable]) -> None:
        """
            Update a lifecycle hook.

            :param hook_name: The name of the hook to update. Must be one
                              of: on_starting, on_reload, when_ready, on_exit.
            :param hook: The new hook callable, or None to remove the hook.

            :raises ValueError: If the hook name is not recognized.
        """
        valid_hooks = {"on_starting", "on_reload", "when_ready", "on_exit"}

        if hook_name not in valid_hooks:
            errmsg = f"Unknown hook '{hook_name}'. Valid hooks: {valid_hooks}"
            raise ValueError(errmsg)

        self._hooks[hook_name] = hook

        return

    def get_exit_code_for_load_error(self) -> int:
        """
            Get the exit code for an application load error.

            :returns: The EXIT_APP_LOAD_ERROR exit code.
        """
        return EXIT_APP_LOAD_ERROR
