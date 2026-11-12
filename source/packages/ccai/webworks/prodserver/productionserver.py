"""
    Production server main module.

    This module provides the ProductionServer class. It is the built-in WSGI
    server (ccai.webworks.wsgi.WSGIServer) with the production layer on top:
    the WSGI server binds the address, parses HTTP/1.1, runs the pre-forked
    worker processes and their threads, terminates TLS, shuts down gracefully
    and replaces workers that end; the production server adds

    - its ServerConfig (gunicorn-style options, see ServerConfig.to_wsgi_config),
    - process management: working directory, daemon mode, the PID file, and
      dropping privileges once the address is bound and before any
      application code runs,
    - the production request pipeline (ProductionMiddleware): request IDs,
      health and metrics endpoints, the structured access log, header and
      time limits, the HTTPS redirect, memory-limit recycling,
    - the TLS policy of SSLManager (minimum version, ciphers, client
      certificates) on the listener,
    - application loading in the master (preload, or an object given to the
      server) or in every worker (an application factory without preload),
    - lifecycle hooks: on_starting, when_ready, on_reload, on_exit,
    - signals: SIGTERM and SIGINT shut down gracefully, SIGHUP replaces the
      workers without dropping connections.

    Serving a WebApplication::

        from ccai.webworks.prodserver import ProductionServer, ServerConfig

        server = ProductionServer(webapp, ServerConfig(port=8000, workers=4))
        exit_code = server.serve()

    The production server forks its workers, so it needs a POSIX platform.
"""

import logging
import os
import sys

from typing import Any, Callable, Dict, Iterable, Optional

from ccai.errors.exceptions import SemanticError

from ccai.webworks.prodserver.applicationloader import ApplicationLoader, ApplicationLoadError
from ccai.webworks.prodserver.exceptions import ConfigurationError
from ccai.webworks.prodserver.healthchecker import HealthChecker
from ccai.webworks.prodserver.metricscollector import MetricsCollector
from ccai.webworks.prodserver.metricsstore import MetricsStore
from ccai.webworks.prodserver.processmanager import ProcessManager, PidFileError
from ccai.webworks.prodserver.productionmiddleware import ProductionMiddleware
from ccai.webworks.prodserver.requesttracer import RequestTracer
from ccai.webworks.prodserver.resourcelimiter import ResourceLimiter
from ccai.webworks.prodserver.serverconfig import (
    ServerConfig,
    ServerState,
    EXIT_SUCCESS,
    EXIT_ERROR,
    EXIT_BIND_ERROR,
    EXIT_APP_LOAD_ERROR,
    EXIT_PID_FILE_ERROR,
)
from ccai.webworks.prodserver.sslmanager import SSLManager, SSLConfigError
from ccai.webworks.prodserver.structuredlogger import StructuredLogger
from ccai.webworks.wsgi.application import as_wsgi_application
from ccai.webworks.wsgi.exceptions import BindError
from ccai.webworks.wsgi.server import WSGIServer
from ccai.webworks.wsgi.serverconfig import ServerConfig as WSGIServerConfig
from ccai.webworks.wsgi.workermanager import WorkerManager


# Default logger for production server
_logger = logging.getLogger("webworks.prodserver")


class _WorkerLoadedApplication:
    """
        A WSGI application that is created in each worker process.

        Used when the application comes from a factory and is not preloaded:
        every worker calls the factory once, before it accepts connections.
    """

    def __init__(self, loader: ApplicationLoader):
        """
            Construct the per-worker application.

            :param loader: The loader holding the application factory.
        """
        self._loader = loader
        self._app: Optional[Callable[..., Iterable[bytes]]] = None
        return

    @property
    def can_serve(self) -> bool:
        """
            Check whether the application of this worker passes requests on.

            :returns: False before the application was loaded, else what the
                application reports (True for a plain WSGI application).
        """
        if self._app is None:
            rtnval = False
        else:
            rtnval = getattr(self._app, "can_serve", True) is True
        return rtnval

    def on_worker_start(self, worker: Any) -> None:
        """
            Load the application in this worker and start it.

            :param worker: The WSGI worker that is starting.

            :raises ApplicationLoadError: If the factory fails; the worker
                does not boot and the server stops.
        """
        loaded = self._loader.get_app_for_worker()
        self._app = as_wsgi_application(loaded)

        start_hook = getattr(self._app, "on_worker_start", None)
        if start_hook is not None:
            start_hook(worker)

        return

    def on_worker_exit(self, worker: Any) -> None:
        """
            Stop the application of this worker.

            :param worker: The WSGI worker that has stopped serving.
        """
        exit_hook = getattr(self._app, "on_worker_exit", None)
        if exit_hook is not None:
            exit_hook(worker)
        return

    def __call__(self, environ: Dict[str, Any], start_response: Callable[..., Any]) -> Iterable[bytes]:
        """
            Serve a request with the application of this worker.

            :param environ: The WSGI environ.
            :param start_response: The WSGI start_response callable.

            :returns: The response body.
        """
        rtnval = self._app(environ, start_response)
        return rtnval


class ProductionServer(WSGIServer):
    """
        The production server: the built-in WSGI server with the production
        layer on top. See the module documentation.
    """

    def __init__(
        self,
        app: Optional[object] = None,
        config: Optional[ServerConfig] = None,
        app_factory: Optional[Callable[[], object]] = None,
    ):
        """
            Construct a ProductionServer.

            :param app: The application to serve: a WebApplication, an ASGI
                application, or a WSGI callable. It has been loaded already, so
                it is shared by the workers whatever 'preload' says.
            :param config: Server configuration. Uses defaults if not provided.
            :param app_factory: A callable without arguments that returns the
                application. With 'preload' it is called once in the master
                before the workers are forked, otherwise once in every worker.
                Give either this or app.

            :raises SemanticError: If not exactly one of app and app_factory
                is given.
        """
        if (app is None) == (app_factory is None):
            errmsg = "ProductionServer needs exactly one of 'app' and 'app_factory'."
            raise SemanticError(errmsg)

        if config is None:
            config = ServerConfig()

        self._server_config = config
        self._application = app
        self._app_factory = app_factory
        self._state: ServerState = ServerState.STOPPED

        # The production components. Each worker process works on its own
        # copy of the ones the request pipeline uses.
        self._structured_logger = StructuredLogger(config)
        self._metrics_collector = MetricsCollector(config)
        self._request_tracer = RequestTracer(config)
        self._health_checker = HealthChecker(config)
        self._ssl_manager = SSLManager(config)
        self._process_manager = ProcessManager(config)
        self._application_loader = ApplicationLoader(config)
        self._resource_limiter = ResourceLimiter(config)
        self._metrics_store: Optional[MetricsStore] = None
        self._middleware: Optional[ProductionMiddleware] = None

        if app_factory is not None:
            self._application_loader.set_factory(app_factory)

        # The WSGI application is the production pipeline, built once the
        # address is bound and the privileges are dropped.
        super().__init__(app=None, config=config.to_wsgi_config())

        return

    # =========================================================================
    # Properties
    # =========================================================================

    @property
    def app(self) -> Optional[object]:
        """
            Get the application given to the server.

            :returns: The application object, or None when a factory was given.
        """
        return self._application

    @property
    def config(self) -> ServerConfig:
        """
            Get the production server configuration.

            :returns: The ServerConfig instance.
        """
        return self._server_config

    @property
    def wsgi_config(self) -> WSGIServerConfig:
        """
            Get the configuration of the WSGI server underneath.

            :returns: The WSGI ServerConfig built from the production configuration.
        """
        return self._config

    @property
    def state(self) -> ServerState:
        """
            Get the current server lifecycle state.

            :returns: The current ServerState.
        """
        return self._state

    @property
    def middleware(self) -> Optional[ProductionMiddleware]:
        """
            Get the production request pipeline.

            :returns: The middleware, or None before the server started.
        """
        return self._middleware

    @property
    def health_checker(self) -> HealthChecker:
        """
            Get the health checker component.

            :returns: The HealthChecker instance.
        """
        return self._health_checker

    @property
    def metrics_collector(self) -> MetricsCollector:
        """
            Get the metrics collector component.

            :returns: The MetricsCollector instance.
        """
        return self._metrics_collector

    @property
    def metrics_store(self) -> Optional[MetricsStore]:
        """
            Get the store that shares the metrics of the workers.

            :returns: The MetricsStore, or None before the server started.
        """
        return self._metrics_store

    @property
    def structured_logger(self) -> StructuredLogger:
        """
            Get the structured logger component.

            :returns: The StructuredLogger instance.
        """
        return self._structured_logger

    @property
    def request_tracer(self) -> RequestTracer:
        """
            Get the request tracer component.

            :returns: The RequestTracer instance.
        """
        return self._request_tracer

    @property
    def ssl_manager(self) -> SSLManager:
        """
            Get the SSL manager component.

            :returns: The SSLManager instance.
        """
        return self._ssl_manager

    @property
    def process_manager(self) -> ProcessManager:
        """
            Get the process manager component.

            :returns: The ProcessManager instance.
        """
        return self._process_manager

    @property
    def application_loader(self) -> ApplicationLoader:
        """
            Get the application loader component.

            :returns: The ApplicationLoader instance.
        """
        return self._application_loader

    @property
    def resource_limiter(self) -> ResourceLimiter:
        """
            Get the resource limiter component.

            :returns: The ResourceLimiter instance.
        """
        return self._resource_limiter

    # =========================================================================
    # Lifecycle
    # =========================================================================

    def serve(self) -> int:
        """
            Run the production server until it is stopped.

            Validates the configuration, then: on_starting hook, working
            directory, daemon mode, TLS context, bind, PID file, log files,
            privilege drop, worker temp directory, application loading,
            workers, when_ready hook. Blocks until SIGTERM, SIGINT or stop(),
            shuts down gracefully, calls the on_exit hook and removes the PID
            file.

            :returns: Exit code: EXIT_SUCCESS, EXIT_BIND_ERROR,
                EXIT_PID_FILE_ERROR, EXIT_APP_LOAD_ERROR (the application could
                not be loaded, in the master or in a worker) or EXIT_ERROR.

            :raises ConfigurationError: If the configuration is invalid, the
                TLS certificate cannot be loaded, or the platform cannot fork
                workers.
        """
        if self._state != ServerState.STOPPED:
            _logger.warning(
                "Cannot start server in state %s, must be STOPPED",
                self._state.value,
            )
            return EXIT_ERROR

        self._validate_before_start()

        self._config = self._server_config.to_wsgi_config()
        self._state = ServerState.STARTING

        _logger.info("Production server starting")

        exit_code = EXIT_SUCCESS

        try:
            self._application_loader.call_on_starting()

            self._process_manager.change_directory()
            self._process_manager.daemonize()

            self.serve_forever()

            if self.boot_failed:
                _logger.error("A worker could not load the application, the server stopped")
                exit_code = EXIT_APP_LOAD_ERROR

        except BindError as bind_err:
            _logger.error("Cannot bind the server address: %s", bind_err)
            exit_code = EXIT_BIND_ERROR
        except PidFileError as pid_err:
            _logger.error("PID file error: %s", pid_err)
            exit_code = EXIT_PID_FILE_ERROR
        except ApplicationLoadError as load_err:
            _logger.error("Application load error: %s", load_err)
            exit_code = EXIT_APP_LOAD_ERROR
        finally:
            self._release()
            self._state = ServerState.STOPPED

        _logger.info("Production server stopped (exit code %d)", exit_code)

        return exit_code

    def stop(self, graceful: bool = True) -> None:
        """
            Stop the production server.

            Safe to call from another thread. With graceful True, the requests
            in flight get the graceful timeout to finish.

            :param graceful: If True, allow in-flight requests to complete.
        """
        if self._state in (ServerState.STOPPED, ServerState.SHUTTING_DOWN):
            return

        self._state = ServerState.SHUTTING_DOWN
        self.shutdown(graceful=graceful)
        return

    def reload(self) -> None:
        """
            Ask for the workers to be replaced, as SIGHUP does.

            The main loop calls the on_reload hook and starts fresh workers
            before it stops the old ones gracefully, so no connection is
            dropped.
        """
        if self._state != ServerState.RUNNING:
            _logger.warning(
                "Cannot reload in state %s, must be RUNNING",
                self._state.value,
            )
            return

        self._reload_requested = True
        return

    def _validate_before_start(self) -> None:
        """
            Check everything that has to hold before the server starts.

            :raises ConfigurationError: If something does not hold.
        """
        self._server_config.validate()

        if not hasattr(os, "fork"):
            errors = [
                f"The production server forks its worker processes, which {sys.platform} cannot do. "
                f"Serve the application's wsgi_app with a WSGI server for this platform, "
                f"or its asgi_app with an ASGI server."
            ]
            raise ConfigurationError(errors)

        try:
            self._ssl_manager.validate_config()
            if self._ssl_manager.is_ssl_enabled:
                # The private key is commonly readable by root only, so it is
                # loaded before the privileges are dropped.
                self._ssl_manager.create_ssl_context()
        except SSLConfigError as ssl_err:
            raise ConfigurationError([str(ssl_err)]) from ssl_err

        return

    # =========================================================================
    # WSGIServer hooks
    # =========================================================================

    def _setup_ssl(self) -> None:
        """
            Install the TLS context of the SSLManager on the listener.
        """
        ssl_context = self._ssl_manager.ssl_context
        if ssl_context is not None:
            self._listener.set_ssl_context(ssl_context)
        return

    def _after_bind(self) -> None:
        """
            Finish the startup that needs the bound address.

            The PID file and the log files may live where only the user the
            server was started as can write, so they come first; then the
            privileges are dropped, and everything after that (the worker temp
            directory, loading the application) runs without them.

            :raises PidFileError: If another server holds the PID file.
            :raises ApplicationLoadError: If the application cannot be loaded.
        """
        self._process_manager.write_pid_file()
        self._structured_logger.open_log_files()

        self._process_manager.drop_privileges()

        tmp_dir = self._resource_limiter.setup_worker_tmp_dir()
        self._metrics_store = MetricsStore(tmp_dir, self._server_config)

        application = self._load_application()

        self._middleware = ProductionMiddleware(
            application,
            self._server_config,
            health_checker=self._health_checker,
            metrics_collector=self._metrics_collector,
            metrics_store=self._metrics_store,
            request_tracer=self._request_tracer,
            structured_logger=self._structured_logger,
            resource_limiter=self._resource_limiter,
            ssl_manager=self._ssl_manager,
        )
        self._app = self._middleware

        return

    def _load_application(self) -> Callable[..., Iterable[bytes]]:
        """
            Get the WSGI application the workers serve.

            :returns: The application loaded here, or one each worker loads.

            :raises ApplicationLoadError: If the factory fails in the master.
        """
        if self._application is not None:
            self._application_loader.set_app(self._application)
            rtnval = as_wsgi_application(self._application)
        elif self._server_config.preload:
            loaded = self._application_loader.preload()
            rtnval = as_wsgi_application(loaded)
        else:
            rtnval = _WorkerLoadedApplication(self._application_loader)

        return rtnval

    def _create_worker_manager(self) -> WorkerManager:
        """
            Build the worker manager, telling the server when a worker ended.

            :returns: The WorkerManager.
        """
        rtnval = WorkerManager(
            self._app,
            self._listener,
            self._config,
            exit_callback=self._worker_ended,
        )
        return rtnval

    def _after_spawn(self) -> None:
        """
            The workers are running: call the when_ready hook.
        """
        self._state = ServerState.RUNNING
        self._health_checker.set_server_state(ServerState.RUNNING)
        self._application_loader.call_when_ready()

        _logger.info(
            "Production server started on %s with %d worker(s)",
            self._get_bind_address(),
            self._config.workers,
        )
        return

    def _worker_ended(self, pid: int, worker_id: int, exit_code: Optional[int]) -> None:
        """
            Fold the metrics of a worker that ended into the totals.

            :param pid: PID of the worker process.
            :param worker_id: ID of the worker.
            :param exit_code: Its exit code, None when a signal ended it.
        """
        if self._metrics_store is not None:
            self._metrics_store.retire_worker(pid)
        return

    def _handle_sigint(self, signum: int, frame: Any) -> None:
        """
            Handle SIGINT: shut down gracefully, as SIGTERM does.

            :param signum: Signal number.
            :param frame: Current stack frame.
        """
        self._shutdown_graceful = True
        self._shutdown_requested = True
        return

    def _handle_reload(self) -> None:
        """
            Replace the workers (SIGHUP or reload()).

            New workers start serving before the old ones are asked to stop,
            so no connection is dropped. With an application loaded in the
            master the new workers serve the same code; with a factory and no
            preload each new worker loads the application again.
        """
        self._reload_requested = False

        if self._worker_manager is None:
            return

        self._state = ServerState.RELOADING
        _logger.info("Production server reloading: replacing the workers")

        self._application_loader.call_on_reload()
        self._worker_manager.replace_workers()

        self._state = ServerState.RUNNING
        return

    def _release(self) -> None:
        """
            Release what the server holds once it has stopped.

            Calls the on_exit hook, removes the PID file and the worker temp
            directory and closes the log files.
        """
        self._application_loader.call_on_exit()
        self._process_manager.cleanup_pid_file()
        self._structured_logger.close_log_files()
        self._resource_limiter.cleanup_worker_tmp_dir()
        self._process_manager.restore_directory()
        return

    # =========================================================================
    # Status
    # =========================================================================

    def get_status(self) -> Dict[str, Any]:
        """
            Get server status information.

            :returns: Dictionary with the state, the address, the workers and
                the status of the components.
        """
        status: Dict[str, Any] = {
            "state": self._state.value,
            "host": self._server_config.host,
            "port": self._server_config.port,
            "ssl": self._ssl_manager.get_status(),
            "process": self._process_manager.get_status(),
            "resources": self._resource_limiter.get_status(),
        }

        if self._worker_manager is not None:
            status["workers"] = self._worker_manager.get_worker_stats()

        if self._listener is not None:
            status["bound_address"] = self._listener.bound_address

        return status

