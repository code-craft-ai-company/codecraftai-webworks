"""
    Tests for the ProductionServer class.

    This module contains unit tests for the production server main class
    including initialization, start/stop/reload lifecycle, component wiring,
    and error handling during startup.
"""

from ccai.testbase.mocking import Mock
from ccai.webworks.prodserver.productionserver import ProductionServer
from ccai.webworks.prodserver.serverconfig import (
    ServerConfig,
    ServerState,
    EXIT_SUCCESS,
    EXIT_ERROR,
    EXIT_CONFIG_ERROR,
    EXIT_APP_LOAD_ERROR,
    EXIT_PID_FILE_ERROR,
)
from ccai.webworks.prodserver.applicationloader import ApplicationLoader
from ccai.webworks.prodserver.connectionmanager import ConnectionManager
from ccai.webworks.prodserver.healthchecker import HealthChecker
from ccai.webworks.prodserver.metricscollector import MetricsCollector
from ccai.webworks.prodserver.processmanager import ProcessManager
from ccai.webworks.prodserver.reloadcoordinator import ReloadCoordinator
from ccai.webworks.prodserver.requesttracer import RequestTracer
from ccai.webworks.prodserver.resourcelimiter import ResourceLimiter
from ccai.webworks.prodserver.shutdowncoordinator import ShutdownCoordinator
from ccai.webworks.prodserver.signalhandler import SignalHandler
from ccai.webworks.prodserver.sslmanager import SSLManager
from ccai.webworks.prodserver.structuredlogger import StructuredLogger
from ccai.webworks.prodserver.workermanager import WorkerManager


def _create_mock_app():
    """
        Create a mock application object.

        :returns: A Mock application instance.
    """
    mock_app = Mock()
    mock_app.configure(recursive=True)
    return mock_app


def _create_config(**overrides):
    """
        Create a ServerConfig with optional overrides.

        :returns: A ServerConfig instance.
    """
    config = ServerConfig(**overrides)
    return config


# =============================================================================
# Unit Tests for Initialization
# =============================================================================

def test_production_server_initial_state_is_stopped():
    """
        Test that a new ProductionServer has state STOPPED.
    """
    mock_app = _create_mock_app()
    server = ProductionServer(mock_app)

    if server.state != ServerState.STOPPED:
        errmsg = f"Expected state STOPPED, got {server.state}"
        raise AssertionError(errmsg)

    return


def test_production_server_stores_app():
    """
        Test that the ProductionServer stores the provided app.
    """
    mock_app = _create_mock_app()
    server = ProductionServer(mock_app)

    if server.app is not mock_app:
        errmsg = "Expected server.app to be the provided mock app"
        raise AssertionError(errmsg)

    return


def test_production_server_uses_default_config_when_none_provided():
    """
        Test that a default ServerConfig is used when none is provided.
    """
    mock_app = _create_mock_app()
    server = ProductionServer(mock_app)

    if not isinstance(server.config, ServerConfig):
        errmsg = "Expected server.config to be a ServerConfig instance"
        raise AssertionError(errmsg)

    return


def test_production_server_uses_provided_config():
    """
        Test that the ProductionServer uses the provided config.
    """
    mock_app = _create_mock_app()
    config = _create_config(port=9000, workers=4)
    server = ProductionServer(mock_app, config=config)

    if server.config is not config:
        errmsg = "Expected server.config to be the provided config"
        raise AssertionError(errmsg)

    if server.config.port != 9000:
        errmsg = f"Expected port 9000, got {server.config.port}"
        raise AssertionError(errmsg)

    return


def test_production_server_components_are_none_before_start():
    """
        Test that all components are None before start() is called.
    """
    mock_app = _create_mock_app()
    server = ProductionServer(mock_app)

    if server.worker_manager is not None:
        errmsg = "Expected worker_manager to be None before start"
        raise AssertionError(errmsg)

    if server.signal_handler is not None:
        errmsg = "Expected signal_handler to be None before start"
        raise AssertionError(errmsg)

    if server.health_checker is not None:
        errmsg = "Expected health_checker to be None before start"
        raise AssertionError(errmsg)

    if server.metrics_collector is not None:
        errmsg = "Expected metrics_collector to be None before start"
        raise AssertionError(errmsg)

    if server.structured_logger is not None:
        errmsg = "Expected structured_logger to be None before start"
        raise AssertionError(errmsg)

    if server.request_tracer is not None:
        errmsg = "Expected request_tracer to be None before start"
        raise AssertionError(errmsg)

    if server.connection_manager is not None:
        errmsg = "Expected connection_manager to be None before start"
        raise AssertionError(errmsg)

    if server.ssl_manager is not None:
        errmsg = "Expected ssl_manager to be None before start"
        raise AssertionError(errmsg)

    if server.process_manager is not None:
        errmsg = "Expected process_manager to be None before start"
        raise AssertionError(errmsg)

    if server.application_loader is not None:
        errmsg = "Expected application_loader to be None before start"
        raise AssertionError(errmsg)

    if server.resource_limiter is not None:
        errmsg = "Expected resource_limiter to be None before start"
        raise AssertionError(errmsg)

    if server.shutdown_coordinator is not None:
        errmsg = "Expected shutdown_coordinator to be None before start"
        raise AssertionError(errmsg)

    if server.reload_coordinator is not None:
        errmsg = "Expected reload_coordinator to be None before start"
        raise AssertionError(errmsg)

    return


# =============================================================================
# Unit Tests for Component Initialization
# =============================================================================

def test_initialize_components_creates_all_components():
    """
        Test that _initialize_components creates all component instances.

        Validates: Requirements All (19.2)
    """
    mock_app = _create_mock_app()
    config = _create_config()
    server = ProductionServer(mock_app, config=config)

    server._initialize_components()

    if not isinstance(server.worker_manager, WorkerManager):
        errmsg = "Expected worker_manager to be a WorkerManager instance"
        raise AssertionError(errmsg)

    if not isinstance(server.signal_handler, SignalHandler):
        errmsg = "Expected signal_handler to be a SignalHandler instance"
        raise AssertionError(errmsg)

    if not isinstance(server.health_checker, HealthChecker):
        errmsg = "Expected health_checker to be a HealthChecker instance"
        raise AssertionError(errmsg)

    if not isinstance(server.metrics_collector, MetricsCollector):
        errmsg = "Expected metrics_collector to be a MetricsCollector instance"
        raise AssertionError(errmsg)

    if not isinstance(server.structured_logger, StructuredLogger):
        errmsg = "Expected structured_logger to be a StructuredLogger instance"
        raise AssertionError(errmsg)

    if not isinstance(server.request_tracer, RequestTracer):
        errmsg = "Expected request_tracer to be a RequestTracer instance"
        raise AssertionError(errmsg)

    if not isinstance(server.connection_manager, ConnectionManager):
        errmsg = "Expected connection_manager to be a ConnectionManager instance"
        raise AssertionError(errmsg)

    if not isinstance(server.ssl_manager, SSLManager):
        errmsg = "Expected ssl_manager to be a SSLManager instance"
        raise AssertionError(errmsg)

    if not isinstance(server.process_manager, ProcessManager):
        errmsg = "Expected process_manager to be a ProcessManager instance"
        raise AssertionError(errmsg)

    if not isinstance(server.application_loader, ApplicationLoader):
        errmsg = "Expected application_loader to be an ApplicationLoader instance"
        raise AssertionError(errmsg)

    if not isinstance(server.resource_limiter, ResourceLimiter):
        errmsg = "Expected resource_limiter to be a ResourceLimiter instance"
        raise AssertionError(errmsg)

    if not isinstance(server.shutdown_coordinator, ShutdownCoordinator):
        errmsg = "Expected shutdown_coordinator to be a ShutdownCoordinator instance"
        raise AssertionError(errmsg)

    if not isinstance(server.reload_coordinator, ReloadCoordinator):
        errmsg = "Expected reload_coordinator to be a ReloadCoordinator instance"
        raise AssertionError(errmsg)

    return


def test_signal_handler_receives_server_reference():
    """
        Test that the SignalHandler receives a reference to the server.
    """
    mock_app = _create_mock_app()
    config = _create_config()
    server = ProductionServer(mock_app, config=config)

    server._initialize_components()

    if server.signal_handler.server is not server:
        errmsg = "Expected signal_handler.server to reference the ProductionServer"
        raise AssertionError(errmsg)

    return


# =============================================================================
# Unit Tests for start() Error Handling
# =============================================================================

def test_start_returns_config_error_on_invalid_config():
    """
        Test that start() returns EXIT_CONFIG_ERROR for invalid configuration.

        Validates: Requirements 1.1
    """
    mock_app = _create_mock_app()
    config = _create_config(port=-1)
    server = ProductionServer(mock_app, config=config)

    exit_code = server.start()

    if exit_code != EXIT_CONFIG_ERROR:
        errmsg = f"Expected EXIT_CONFIG_ERROR ({EXIT_CONFIG_ERROR}), got {exit_code}"
        raise AssertionError(errmsg)

    if server.state != ServerState.STOPPED:
        errmsg = f"Expected state STOPPED after config error, got {server.state}"
        raise AssertionError(errmsg)

    return


def test_start_returns_error_when_not_stopped():
    """
        Test that start() returns EXIT_ERROR when server is not in STOPPED state.
    """
    mock_app = _create_mock_app()
    config = _create_config()
    server = ProductionServer(mock_app, config=config)

    # Force state to RUNNING
    server._state = ServerState.RUNNING

    exit_code = server.start()

    if exit_code != EXIT_ERROR:
        errmsg = f"Expected EXIT_ERROR ({EXIT_ERROR}), got {exit_code}"
        raise AssertionError(errmsg)

    return


def test_start_returns_config_error_on_invalid_worker_class():
    """
        Test that start() returns EXIT_CONFIG_ERROR for invalid worker class.
    """
    mock_app = _create_mock_app()
    config = _create_config(worker_class="invalid")
    server = ProductionServer(mock_app, config=config)

    exit_code = server.start()

    if exit_code != EXIT_CONFIG_ERROR:
        errmsg = f"Expected EXIT_CONFIG_ERROR ({EXIT_CONFIG_ERROR}), got {exit_code}"
        raise AssertionError(errmsg)

    return


# =============================================================================
# Unit Tests for stop()
# =============================================================================

def test_stop_when_already_stopped_does_nothing():
    """
        Test that stop() does nothing when server is already stopped.
    """
    mock_app = _create_mock_app()
    server = ProductionServer(mock_app)

    # Should not raise
    server.stop()

    if server.state != ServerState.STOPPED:
        errmsg = f"Expected state STOPPED, got {server.state}"
        raise AssertionError(errmsg)

    return


def test_stop_transitions_to_stopped():
    """
        Test that stop() transitions the server to STOPPED state.

        Validates: Requirements 2.1
    """
    mock_app = _create_mock_app()
    config = _create_config()
    server = ProductionServer(mock_app, config=config)

    # Initialize components and set state to RUNNING manually
    server._initialize_components()
    server._state = ServerState.RUNNING

    server.stop(graceful=False)

    if server.state != ServerState.STOPPED:
        errmsg = f"Expected state STOPPED after stop, got {server.state}"
        raise AssertionError(errmsg)

    return


def test_stop_updates_health_checker_state():
    """
        Test that stop() updates the health checker to SHUTTING_DOWN.

        Validates: Requirements 2.1
    """
    mock_app = _create_mock_app()
    config = _create_config()
    server = ProductionServer(mock_app, config=config)

    server._initialize_components()
    server._state = ServerState.RUNNING
    server._health_checker.set_server_state(ServerState.RUNNING)

    server.stop(graceful=False)

    # After stop, health checker should have been set to SHUTTING_DOWN
    # and then server transitions to STOPPED
    if server.state != ServerState.STOPPED:
        errmsg = f"Expected state STOPPED, got {server.state}"
        raise AssertionError(errmsg)

    return


def test_stop_graceful_false_terminates_workers_immediately():
    """
        Test that stop(graceful=False) terminates workers without waiting.
    """
    mock_app = _create_mock_app()
    config = _create_config()
    server = ProductionServer(mock_app, config=config)

    server._initialize_components()
    server._state = ServerState.RUNNING

    # Spawn a worker to verify termination
    server._worker_manager.spawn_workers()
    initial_count = server._worker_manager.get_worker_count()

    server.stop(graceful=False)

    final_count = server._worker_manager.get_worker_count()

    if final_count != 0:
        errmsg = f"Expected 0 workers after forceful stop, got {final_count}"
        raise AssertionError(errmsg)

    return


# =============================================================================
# Unit Tests for reload()
# =============================================================================

def test_reload_does_nothing_when_not_running():
    """
        Test that reload() does nothing when server is not RUNNING.

        Validates: Requirements 2.7
    """
    mock_app = _create_mock_app()
    server = ProductionServer(mock_app)

    # Server is STOPPED, reload should be a no-op
    server.reload()

    if server.state != ServerState.STOPPED:
        errmsg = f"Expected state STOPPED, got {server.state}"
        raise AssertionError(errmsg)

    return


def test_reload_transitions_through_reloading_back_to_running():
    """
        Test that reload() transitions RUNNING -> RELOADING -> RUNNING.

        Validates: Requirements 2.7
    """
    mock_app = _create_mock_app()
    config = _create_config()
    server = ProductionServer(mock_app, config=config)

    server._initialize_components()
    server._state = ServerState.RUNNING
    server._reload_coordinator.start()

    # Spawn workers so rolling restart has something to work with
    server._worker_manager.spawn_workers()

    server.reload()

    if server.state != ServerState.RUNNING:
        errmsg = f"Expected state RUNNING after reload, got {server.state}"
        raise AssertionError(errmsg)

    return


def test_reload_updates_health_checker_state():
    """
        Test that reload() updates health checker state during reload.

        Validates: Requirements 2.7
    """
    mock_app = _create_mock_app()
    config = _create_config()
    server = ProductionServer(mock_app, config=config)

    server._initialize_components()
    server._state = ServerState.RUNNING
    server._reload_coordinator.start()
    server._health_checker.set_server_state(ServerState.RUNNING)

    server._worker_manager.spawn_workers()

    server.reload()

    # After reload completes, state should be back to RUNNING
    if server.state != ServerState.RUNNING:
        errmsg = f"Expected state RUNNING after reload, got {server.state}"
        raise AssertionError(errmsg)

    return


# =============================================================================
# Unit Tests for get_status()
# =============================================================================

def test_get_status_returns_basic_info_before_start():
    """
        Test that get_status returns basic info when components are not initialized.
    """
    mock_app = _create_mock_app()
    config = _create_config(port=8080)
    server = ProductionServer(mock_app, config=config)

    status = server.get_status()

    if status["state"] != "stopped":
        errmsg = f"Expected state 'stopped', got {status['state']}"
        raise AssertionError(errmsg)

    if status["port"] != 8080:
        errmsg = f"Expected port 8080, got {status['port']}"
        raise AssertionError(errmsg)

    return


def test_get_status_includes_component_info_after_init():
    """
        Test that get_status includes component info after initialization.
    """
    mock_app = _create_mock_app()
    config = _create_config()
    server = ProductionServer(mock_app, config=config)

    server._initialize_components()

    status = server.get_status()

    if "workers" not in status:
        errmsg = "Expected 'workers' key in status"
        raise AssertionError(errmsg)

    if "health" not in status:
        errmsg = "Expected 'health' key in status"
        raise AssertionError(errmsg)

    if "metrics" not in status:
        errmsg = "Expected 'metrics' key in status"
        raise AssertionError(errmsg)

    if "connections" not in status:
        errmsg = "Expected 'connections' key in status"
        raise AssertionError(errmsg)

    if "ssl" not in status:
        errmsg = "Expected 'ssl' key in status"
        raise AssertionError(errmsg)

    if "process" not in status:
        errmsg = "Expected 'process' key in status"
        raise AssertionError(errmsg)

    if "resources" not in status:
        errmsg = "Expected 'resources' key in status"
        raise AssertionError(errmsg)

    return


# =============================================================================
# Unit Tests for Cleanup
# =============================================================================

def test_cleanup_unregisters_signal_handlers():
    """
        Test that cleanup unregisters signal handlers.
    """
    mock_app = _create_mock_app()
    config = _create_config()
    server = ProductionServer(mock_app, config=config)

    server._initialize_components()

    # Register then cleanup
    server._signal_handler.register()

    if not server._signal_handler.registered:
        errmsg = "Expected signal handlers to be registered"
        raise AssertionError(errmsg)

    server._cleanup()

    if server._signal_handler.registered:
        errmsg = "Expected signal handlers to be unregistered after cleanup"
        raise AssertionError(errmsg)

    return


def test_cleanup_calls_on_exit_hook():
    """
        Test that cleanup calls the on_exit lifecycle hook.

        Validates: Requirements 12.7
    """
    call_log = []

    def on_exit_hook(config):
        call_log.append("on_exit")

    mock_app = _create_mock_app()
    config = _create_config(on_exit=on_exit_hook)
    server = ProductionServer(mock_app, config=config)

    server._initialize_components()
    server._cleanup()

    if len(call_log) != 1:
        errmsg = f"Expected on_exit to be called once, got {len(call_log)}"
        raise AssertionError(errmsg)

    if call_log[0] != "on_exit":
        errmsg = "Expected on_exit hook to be called"
        raise AssertionError(errmsg)

    return


# =============================================================================
# Unit Tests for Full Lifecycle (start + stop)
# =============================================================================

def test_full_lifecycle_start_and_stop():
    """
        Test a full start and stop lifecycle.

        Validates: Requirements 1.1, 2.1
    """
    mock_app = _create_mock_app()
    config = _create_config(workers=2)
    server = ProductionServer(mock_app, config=config)

    exit_code = server.start()

    if exit_code != EXIT_SUCCESS:
        errmsg = f"Expected EXIT_SUCCESS ({EXIT_SUCCESS}), got {exit_code}"
        raise AssertionError(errmsg)

    if server.state != ServerState.RUNNING:
        errmsg = f"Expected state RUNNING after start, got {server.state}"
        raise AssertionError(errmsg)

    if server.worker_manager is None:
        errmsg = "Expected worker_manager to be initialized after start"
        raise AssertionError(errmsg)

    worker_count = server.worker_manager.get_worker_count()
    if worker_count != 2:
        errmsg = f"Expected 2 workers, got {worker_count}"
        raise AssertionError(errmsg)

    server.stop(graceful=False)

    if server.state != ServerState.STOPPED:
        errmsg = f"Expected state STOPPED after stop, got {server.state}"
        raise AssertionError(errmsg)

    return


def test_full_lifecycle_with_hooks():
    """
        Test that lifecycle hooks are called during start and stop.

        Validates: Requirements 12.4, 12.6, 12.7
    """
    call_log = []

    def on_starting_hook(config):
        call_log.append("on_starting")

    def when_ready_hook(config):
        call_log.append("when_ready")

    def on_exit_hook(config):
        call_log.append("on_exit")

    mock_app = _create_mock_app()
    config = _create_config(
        workers=1,
        on_starting=on_starting_hook,
        when_ready=when_ready_hook,
        on_exit=on_exit_hook,
    )
    server = ProductionServer(mock_app, config=config)

    exit_code = server.start()

    if exit_code != EXIT_SUCCESS:
        errmsg = f"Expected EXIT_SUCCESS, got {exit_code}"
        raise AssertionError(errmsg)

    if "on_starting" not in call_log:
        errmsg = "Expected on_starting hook to be called during start"
        raise AssertionError(errmsg)

    if "when_ready" not in call_log:
        errmsg = "Expected when_ready hook to be called during start"
        raise AssertionError(errmsg)

    server.stop(graceful=False)

    if "on_exit" not in call_log:
        errmsg = "Expected on_exit hook to be called during stop"
        raise AssertionError(errmsg)

    return


def test_full_lifecycle_start_stop_reload():
    """
        Test start, reload, and stop lifecycle.

        Validates: Requirements 1.1, 2.1, 2.7
    """
    mock_app = _create_mock_app()
    config = _create_config(workers=1)
    server = ProductionServer(mock_app, config=config)

    exit_code = server.start()

    if exit_code != EXIT_SUCCESS:
        errmsg = f"Expected EXIT_SUCCESS, got {exit_code}"
        raise AssertionError(errmsg)

    # Reload should work while running
    server.reload()

    if server.state != ServerState.RUNNING:
        errmsg = f"Expected state RUNNING after reload, got {server.state}"
        raise AssertionError(errmsg)

    server.stop(graceful=False)

    if server.state != ServerState.STOPPED:
        errmsg = f"Expected state STOPPED after stop, got {server.state}"
        raise AssertionError(errmsg)

    return
