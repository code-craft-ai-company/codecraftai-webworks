"""
    Production server main module.

    This module provides the ProductionServer class that orchestrates all
    production server components including worker management, signal handling,
    health checks, metrics collection, structured logging, request tracing,
    connection management, SSL/TLS, process management, application loading,
    and resource limiting.
"""

import logging
import sys
from typing import Any, Callable, Dict, Optional

from automojo.webworks.prodserver.applicationloader import ApplicationLoader, ApplicationLoadError
from automojo.webworks.prodserver.connectionmanager import ConnectionManager
from automojo.webworks.prodserver.exceptions import ConfigurationError, ProductionServerError
from automojo.webworks.prodserver.healthchecker import HealthChecker
from automojo.webworks.prodserver.metricscollector import MetricsCollector
from automojo.webworks.prodserver.processmanager import ProcessManager, PidFileError
from automojo.webworks.prodserver.reloadcoordinator import ReloadCoordinator
from automojo.webworks.prodserver.requesttracer import RequestTracer
from automojo.webworks.prodserver.resourcelimiter import ResourceLimiter
from automojo.webworks.prodserver.serverconfig import (
    ServerConfig,
    ServerState,
    EXIT_SUCCESS,
    EXIT_ERROR,
    EXIT_CONFIG_ERROR,
    EXIT_APP_LOAD_ERROR,
    EXIT_PID_FILE_ERROR,
)
from automojo.webworks.prodserver.shutdowncoordinator import ShutdownCoordinator
from automojo.webworks.prodserver.signalhandler import SignalHandler
from automojo.webworks.prodserver.sslmanager import SSLManager, SSLConfigError
from automojo.webworks.prodserver.structuredlogger import StructuredLogger
from automojo.webworks.prodserver.workermanager import WorkerManager


# Default logger for production server
_logger = logging.getLogger("webworks.prodserver")


class ProductionServer:
    """
        Main production server class that orchestrates all components.

        Coordinates worker management, signal handling, health checks,
        metrics collection, structured logging, request tracing, connection
        management, SSL/TLS, process management, application loading, and
        resource limiting to provide a production-grade server.
    """

    def __init__(self, app: object, config: Optional[ServerConfig] = None):
        """
            Construct a ProductionServer.

            :param app: The web application instance to serve.
            :param config: Server configuration. Uses defaults if not provided.
        """
        self._app = app
        self._config = config if config is not None else ServerConfig()
        self._state: ServerState = ServerState.STOPPED

        # Components are initialized lazily during start()
        self._worker_manager: Optional[WorkerManager] = None
        self._signal_handler: Optional[SignalHandler] = None
        self._health_checker: Optional[HealthChecker] = None
        self._metrics_collector: Optional[MetricsCollector] = None
        self._structured_logger: Optional[StructuredLogger] = None
        self._request_tracer: Optional[RequestTracer] = None
        self._connection_manager: Optional[ConnectionManager] = None
        self._ssl_manager: Optional[SSLManager] = None
        self._process_manager: Optional[ProcessManager] = None
        self._application_loader: Optional[ApplicationLoader] = None
        self._resource_limiter: Optional[ResourceLimiter] = None
        self._shutdown_coordinator: Optional[ShutdownCoordinator] = None
        self._reload_coordinator: Optional[ReloadCoordinator] = None

        return

    # =========================================================================
    # Properties
    # =========================================================================

    @property
    def app(self) -> object:
        """
            Get the web application instance.

            :returns: The application object.
        """
        return self._app

    @property
    def config(self) -> ServerConfig:
        """
            Get the server configuration.

            :returns: The ServerConfig instance.
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
    def worker_manager(self) -> Optional[WorkerManager]:
        """
            Get the worker manager component.

            :returns: The WorkerManager instance, or None if not initialized.
        """
        return self._worker_manager

    @property
    def signal_handler(self) -> Optional[SignalHandler]:
        """
            Get the signal handler component.

            :returns: The SignalHandler instance, or None if not initialized.
        """
        return self._signal_handler

    @property
    def health_checker(self) -> Optional[HealthChecker]:
        """
            Get the health checker component.

            :returns: The HealthChecker instance, or None if not initialized.
        """
        return self._health_checker

    @property
    def metrics_collector(self) -> Optional[MetricsCollector]:
        """
            Get the metrics collector component.

            :returns: The MetricsCollector instance, or None if not initialized.
        """
        return self._metrics_collector

    @property
    def structured_logger(self) -> Optional[StructuredLogger]:
        """
            Get the structured logger component.

            :returns: The StructuredLogger instance, or None if not initialized.
        """
        return self._structured_logger

    @property
    def request_tracer(self) -> Optional[RequestTracer]:
        """
            Get the request tracer component.

            :returns: The RequestTracer instance, or None if not initialized.
        """
        return self._request_tracer

    @property
    def connection_manager(self) -> Optional[ConnectionManager]:
        """
            Get the connection manager component.

            :returns: The ConnectionManager instance, or None if not initialized.
        """
        return self._connection_manager

    @property
    def ssl_manager(self) -> Optional[SSLManager]:
        """
            Get the SSL manager component.

            :returns: The SSLManager instance, or None if not initialized.
        """
        return self._ssl_manager

    @property
    def process_manager(self) -> Optional[ProcessManager]:
        """
            Get the process manager component.

            :returns: The ProcessManager instance, or None if not initialized.
        """
        return self._process_manager

    @property
    def application_loader(self) -> Optional[ApplicationLoader]:
        """
            Get the application loader component.

            :returns: The ApplicationLoader instance, or None if not initialized.
        """
        return self._application_loader

    @property
    def resource_limiter(self) -> Optional[ResourceLimiter]:
        """
            Get the resource limiter component.

            :returns: The ResourceLimiter instance, or None if not initialized.
        """
        return self._resource_limiter

    @property
    def shutdown_coordinator(self) -> Optional[ShutdownCoordinator]:
        """
            Get the shutdown coordinator component.

            :returns: The ShutdownCoordinator instance, or None if not initialized.
        """
        return self._shutdown_coordinator

    @property
    def reload_coordinator(self) -> Optional[ReloadCoordinator]:
        """
            Get the reload coordinator component.

            :returns: The ReloadCoordinator instance, or None if not initialized.
        """
        return self._reload_coordinator


    # =========================================================================
    # Lifecycle Methods
    # =========================================================================

    def start(self) -> int:
        """
            Start the production server.

            Performs the full startup sequence:
            1. Validate configuration.
            2. Initialize all components.
            3. Handle process management (PID file, daemon, privileges, chdir).
            4. Preload application if configured.
            5. Call on_starting lifecycle hook.
            6. Set up SSL context if configured.
            7. Register signal handlers.
            8. Spawn workers.
            9. Start worker monitoring.
            10. Call when_ready lifecycle hook.

            :returns: Exit code (0 for success, non-zero for errors).
        """
        if self._state != ServerState.STOPPED:
            _logger.warning(
                "Cannot start server in state %s, must be STOPPED",
                self._state.value,
            )
            return EXIT_ERROR

        self._state = ServerState.STARTING

        _logger.info("Production server starting")

        try:
            self._config.validate()
        except ConfigurationError as exc:
            _logger.error("Configuration validation failed: %s", exc)
            self._state = ServerState.STOPPED
            return EXIT_CONFIG_ERROR

        self._initialize_components()

        # Process management: PID file, daemon, privileges, chdir
        try:
            self._process_manager.change_directory()
            self._process_manager.daemonize()
            self._process_manager.write_pid_file()
            self._process_manager.drop_privileges()
        except PidFileError as exc:
            _logger.error("PID file error: %s", exc)
            self._state = ServerState.STOPPED
            return EXIT_PID_FILE_ERROR
        except Exception as exc:
            _logger.error("Process management error: %s", exc)
            self._state = ServerState.STOPPED
            return EXIT_ERROR

        # Preload application if configured
        try:
            self._application_loader.preload(app=self._app)
        except ApplicationLoadError as exc:
            _logger.error("Application load error: %s", exc)
            self._cleanup_on_start_failure()
            return EXIT_APP_LOAD_ERROR

        # Call on_starting hook
        self._application_loader.call_on_starting()

        # Set up SSL if configured
        if self._ssl_manager.is_ssl_enabled:
            try:
                self._ssl_manager.create_ssl_context()
            except SSLConfigError as exc:
                _logger.error("SSL configuration error: %s", exc)
                self._cleanup_on_start_failure()
                return EXIT_CONFIG_ERROR

        # Open log files
        self._structured_logger.open_log_files()

        # Set up resource limiter temp directory
        self._resource_limiter.setup_worker_tmp_dir()

        # Register signal handlers
        self._signal_handler.register()

        # Spawn workers
        self._worker_manager.spawn_workers()

        # Start worker monitoring
        self._worker_manager.start_monitor()

        # Transition to running
        self._state = ServerState.RUNNING

        # Update health checker with running state
        self._health_checker.set_server_state(ServerState.RUNNING)

        # Start shutdown and reload coordinators
        self._shutdown_coordinator.start()
        self._reload_coordinator.start()

        # Call when_ready hook
        self._application_loader.call_when_ready()

        _logger.info(
            "Production server started on %s:%d with %d worker(s)",
            self._config.host,
            self._config.port,
            self._worker_manager.get_worker_count(),
        )

        return EXIT_SUCCESS

    def stop(self, graceful: bool = True) -> None:
        """
            Stop the production server.

            When graceful is True, allows in-flight requests to complete
            within the graceful timeout before terminating workers. When
            False, terminates workers immediately.

            :param graceful: If True, allow in-flight requests to complete.
        """
        if self._state == ServerState.STOPPED:
            _logger.warning("Server is already stopped")
            return

        if self._state == ServerState.SHUTTING_DOWN:
            _logger.warning("Server is already shutting down")
            return

        _logger.info(
            "Production server stopping (graceful=%s)",
            graceful,
        )

        self._state = ServerState.SHUTTING_DOWN

        # Update health checker state
        if self._health_checker is not None:
            self._health_checker.set_server_state(ServerState.SHUTTING_DOWN)

        if graceful and self._shutdown_coordinator is not None:
            self._shutdown_coordinator.initiate_shutdown()
        elif self._worker_manager is not None:
            self._worker_manager.terminate_all(graceful=False)

        self._cleanup()

        self._state = ServerState.STOPPED

        _logger.info("Production server stopped")

        return

    def reload(self) -> None:
        """
            Reload configuration without dropping connections.

            Performs a rolling restart of workers via the reload
            coordinator. Calls the on_reload lifecycle hook.
        """
        if self._state != ServerState.RUNNING:
            _logger.warning(
                "Cannot reload in state %s, must be RUNNING",
                self._state.value,
            )
            return

        _logger.info("Production server reloading configuration")

        self._state = ServerState.RELOADING

        if self._health_checker is not None:
            self._health_checker.set_server_state(ServerState.RELOADING)

        if self._reload_coordinator is not None:
            self._reload_coordinator.reload()

        self._state = ServerState.RUNNING

        if self._health_checker is not None:
            self._health_checker.set_server_state(ServerState.RUNNING)

        _logger.info("Production server reload complete")

        return


    # =========================================================================
    # Component Initialization
    # =========================================================================

    def _initialize_components(self) -> None:
        """
            Initialize all server components.

            Creates instances of all subsystems using the current
            configuration. Components that depend on other components
            receive references during initialization.
        """
        config = self._config

        # Core components
        self._structured_logger = StructuredLogger(config)
        self._metrics_collector = MetricsCollector(config)
        self._request_tracer = RequestTracer(config)
        self._connection_manager = ConnectionManager(config)
        self._health_checker = HealthChecker(config)
        self._ssl_manager = SSLManager(config)
        self._process_manager = ProcessManager(config)
        self._application_loader = ApplicationLoader(config)
        self._resource_limiter = ResourceLimiter(config)

        # Worker manager needs config and app
        self._worker_manager = WorkerManager(config, self._app)

        # Signal handler needs a reference to this server
        self._signal_handler = SignalHandler(self)

        # Coordinators need config and worker manager
        self._shutdown_coordinator = ShutdownCoordinator(config, self._worker_manager)
        self._reload_coordinator = ReloadCoordinator(config, self._worker_manager)

        _logger.info("All server components initialized")

        return

    # =========================================================================
    # Cleanup
    # =========================================================================

    def _cleanup(self) -> None:
        """
            Clean up all server resources during shutdown.

            Stops the worker monitor, unregisters signal handlers,
            calls the on_exit hook, cleans up the PID file, closes
            log files, and cleans up the resource limiter temp directory.
        """
        # Stop worker monitoring
        if self._worker_manager is not None:
            self._worker_manager.stop_monitor()

        # Unregister signal handlers
        if self._signal_handler is not None:
            self._signal_handler.unregister()

        # Call on_exit hook
        if self._application_loader is not None:
            self._application_loader.call_on_exit()

        # Clean up PID file
        if self._process_manager is not None:
            self._process_manager.cleanup_pid_file()

        # Close log files
        if self._structured_logger is not None:
            self._structured_logger.close_log_files()

        # Clean up resource limiter temp directory
        if self._resource_limiter is not None:
            self._resource_limiter.cleanup_worker_tmp_dir()

        return

    def _cleanup_on_start_failure(self) -> None:
        """
            Clean up resources when startup fails partway through.

            Performs a subset of cleanup for resources that may have
            been initialized before the failure occurred.
        """
        if self._process_manager is not None:
            self._process_manager.cleanup_pid_file()

        self._state = ServerState.STOPPED

        return

    # =========================================================================
    # Status
    # =========================================================================

    def get_status(self) -> Dict[str, Any]:
        """
            Get comprehensive server status information.

            Aggregates status from all components into a single
            status dictionary.

            :returns: Dictionary with server status information.
        """
        status: Dict[str, Any] = {
            "state": self._state.value,
            "host": self._config.host,
            "port": self._config.port,
        }

        if self._worker_manager is not None:
            status["workers"] = {
                "count": self._worker_manager.get_worker_count(),
                "statuses": {
                    wid: ws.as_dict()
                    for wid, ws in self._worker_manager.get_worker_status().items()
                },
            }

        if self._health_checker is not None:
            status["health"] = self._health_checker.get_status()

        if self._metrics_collector is not None:
            status["metrics"] = self._metrics_collector.get_metrics_summary()

        if self._connection_manager is not None:
            status["connections"] = self._connection_manager.get_status()

        if self._ssl_manager is not None:
            status["ssl"] = self._ssl_manager.get_status()

        if self._process_manager is not None:
            status["process"] = self._process_manager.get_status()

        if self._resource_limiter is not None:
            status["resources"] = self._resource_limiter.get_status()

        return status
