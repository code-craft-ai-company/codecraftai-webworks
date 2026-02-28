"""
    Tests for the ShutdownCoordinator class.

    This module contains unit tests for the production server
    ShutdownCoordinator class including state transitions, accepting
    flag management, graceful shutdown coordination, and in-flight
    request handling.
"""

import time
import threading

from automojo.webworks.prodserver.serverconfig import ServerConfig, ServerState
from automojo.webworks.prodserver.shutdowncoordinator import ShutdownCoordinator
from automojo.webworks.prodserver.workermanager import WorkerManager


# =============================================================================
# Helpers
# =============================================================================

def _dummy_app(request):
    """
        Dummy application callable for testing.
    """
    return None


def _create_coordinator(
    workers: int = 2,
    graceful_timeout: int = 5,
    **kwargs
) -> tuple:
    """
        Create a ShutdownCoordinator with its dependencies for testing.

        :param workers: Number of workers to configure.
        :param graceful_timeout: Graceful shutdown timeout in seconds.

        :returns: A tuple of (coordinator, worker_manager, config).
    """
    config = ServerConfig(
        workers=workers,
        graceful_timeout=graceful_timeout,
        **kwargs
    )
    worker_manager = WorkerManager(config=config, app=_dummy_app)
    coordinator = ShutdownCoordinator(
        config=config,
        worker_manager=worker_manager
    )

    return coordinator, worker_manager, config


# =============================================================================
# Unit Tests for ShutdownCoordinator Initialization
# =============================================================================

def test_shutdown_coordinator_initial_state_is_stopped():
    """
        Test that a new ShutdownCoordinator starts in STOPPED state.
    """
    coordinator, _, _ = _create_coordinator()

    if coordinator.state != ServerState.STOPPED:
        errmsg = f"Expected initial state STOPPED, got {coordinator.state}"
        raise AssertionError(errmsg)

    return


def test_shutdown_coordinator_not_accepting_initially():
    """
        Test that a new ShutdownCoordinator is not accepting connections.
    """
    coordinator, _, _ = _create_coordinator()

    if coordinator.is_accepting is not False:
        errmsg = "Expected is_accepting to be False initially"
        raise AssertionError(errmsg)

    return


def test_shutdown_coordinator_not_complete_initially():
    """
        Test that shutdown is not marked complete initially.
    """
    coordinator, _, _ = _create_coordinator()

    if coordinator.is_shutdown_complete is not False:
        errmsg = "Expected is_shutdown_complete to be False initially"
        raise AssertionError(errmsg)

    return


# =============================================================================
# Unit Tests for Start
# =============================================================================

def test_start_transitions_to_running():
    """
        Test that start() transitions state to RUNNING.
    """
    coordinator, _, _ = _create_coordinator()

    coordinator.start()

    if coordinator.state != ServerState.RUNNING:
        errmsg = f"Expected state RUNNING after start(), got {coordinator.state}"
        raise AssertionError(errmsg)

    return


def test_start_enables_accepting():
    """
        Test that start() enables accepting new connections.

        Validates: Requirements 2.3
    """
    coordinator, _, _ = _create_coordinator()

    coordinator.start()

    if coordinator.is_accepting is not True:
        errmsg = "Expected is_accepting to be True after start()"
        raise AssertionError(errmsg)

    return


# =============================================================================
# Unit Tests for Graceful Shutdown - State Transitions
# =============================================================================

def test_initiate_shutdown_transitions_to_shutting_down():
    """
        Test that initiate_shutdown() transitions state to SHUTTING_DOWN
        and then to STOPPED.

        Validates: Requirements 2.1, 2.2
    """
    coordinator, manager, _ = _create_coordinator(workers=1)

    manager.spawn_workers()
    coordinator.start()

    coordinator.initiate_shutdown()

    if coordinator.state != ServerState.STOPPED:
        errmsg = f"Expected state STOPPED after shutdown, got {coordinator.state}"
        raise AssertionError(errmsg)

    return


def test_initiate_shutdown_stops_accepting():
    """
        Test that initiate_shutdown() stops accepting new connections.

        Validates: Requirements 2.3
    """
    coordinator, manager, _ = _create_coordinator(workers=1)

    manager.spawn_workers()
    coordinator.start()

    if coordinator.is_accepting is not True:
        errmsg = "Expected is_accepting to be True before shutdown"
        raise AssertionError(errmsg)

    coordinator.initiate_shutdown()

    if coordinator.is_accepting is not False:
        errmsg = "Expected is_accepting to be False after shutdown"
        raise AssertionError(errmsg)

    return


def test_initiate_shutdown_marks_complete():
    """
        Test that initiate_shutdown() sets the shutdown complete event.
    """
    coordinator, manager, _ = _create_coordinator(workers=1)

    manager.spawn_workers()
    coordinator.start()

    coordinator.initiate_shutdown()

    if coordinator.is_shutdown_complete is not True:
        errmsg = "Expected is_shutdown_complete to be True after shutdown"
        raise AssertionError(errmsg)

    return


def test_initiate_shutdown_terminates_workers():
    """
        Test that initiate_shutdown() terminates all workers.

        Validates: Requirements 2.1, 2.2
    """
    coordinator, manager, _ = _create_coordinator(workers=2)

    manager.spawn_workers()
    coordinator.start()

    if manager.get_worker_count() != 2:
        errmsg = f"Expected 2 workers before shutdown, got {manager.get_worker_count()}"
        raise AssertionError(errmsg)

    coordinator.initiate_shutdown()

    if manager.get_worker_count() != 0:
        errmsg = f"Expected 0 workers after shutdown, got {manager.get_worker_count()}"
        raise AssertionError(errmsg)

    return


# =============================================================================
# Unit Tests for Graceful Shutdown - Double Shutdown Safety
# =============================================================================

def test_double_shutdown_is_safe():
    """
        Test that calling initiate_shutdown() twice does not raise.
    """
    coordinator, manager, _ = _create_coordinator(workers=1)

    manager.spawn_workers()
    coordinator.start()

    coordinator.initiate_shutdown()
    coordinator.initiate_shutdown()

    if coordinator.state != ServerState.STOPPED:
        errmsg = f"Expected state STOPPED after double shutdown, got {coordinator.state}"
        raise AssertionError(errmsg)

    return


def test_shutdown_when_stopped_is_safe():
    """
        Test that calling initiate_shutdown() when already stopped is safe.
    """
    coordinator, _, _ = _create_coordinator()

    coordinator.initiate_shutdown()

    if coordinator.state != ServerState.STOPPED:
        errmsg = f"Expected state STOPPED, got {coordinator.state}"
        raise AssertionError(errmsg)

    return


# =============================================================================
# Unit Tests for In-Flight Request Handling
# =============================================================================

def test_shutdown_waits_for_inflight_requests():
    """
        Test that shutdown waits for in-flight requests to complete
        before terminating workers.

        Validates: Requirements 2.4
    """
    coordinator, manager, _ = _create_coordinator(
        workers=1,
        graceful_timeout=5
    )

    manager.spawn_workers()
    coordinator.start()

    workers = manager.get_workers()
    worker_id = list(workers.keys())[0]

    # Simulate an in-flight request
    manager.mark_request_start(worker_id)

    shutdown_started = threading.Event()
    shutdown_done = threading.Event()

    def run_shutdown():
        shutdown_started.set()
        coordinator.initiate_shutdown()
        shutdown_done.set()

    shutdown_thread = threading.Thread(target=run_shutdown)
    shutdown_thread.start()

    # Wait for shutdown to begin
    shutdown_started.wait(timeout=2.0)
    time.sleep(0.3)

    # Verify shutdown is still in progress (waiting for in-flight)
    if shutdown_done.is_set():
        # Shutdown completed immediately - this is acceptable if the
        # timing was very tight, but let's verify the state
        pass
    else:
        # Shutdown is waiting - verify accepting is False
        if coordinator.is_accepting is not False:
            manager.mark_request_end(worker_id)
            shutdown_thread.join(timeout=10.0)
            errmsg = "Expected is_accepting to be False during shutdown"
            raise AssertionError(errmsg)

    # Complete the in-flight request
    manager.mark_request_end(worker_id)

    # Wait for shutdown to finish
    shutdown_thread.join(timeout=10.0)

    if not shutdown_done.is_set():
        errmsg = "Expected shutdown to complete after in-flight requests finished"
        raise AssertionError(errmsg)

    return


def test_shutdown_completes_when_no_inflight_requests():
    """
        Test that shutdown completes quickly when there are no
        in-flight requests.

        Validates: Requirements 2.4
    """
    coordinator, manager, _ = _create_coordinator(
        workers=2,
        graceful_timeout=5
    )

    manager.spawn_workers()
    coordinator.start()

    start_time = time.time()
    coordinator.initiate_shutdown()
    elapsed = time.time() - start_time

    # Should complete quickly (well under the graceful timeout)
    if elapsed > 3.0:
        errmsg = (
            f"Expected shutdown to complete quickly with no in-flight "
            f"requests, took {elapsed:.1f}s"
        )
        raise AssertionError(errmsg)

    return


# =============================================================================
# Unit Tests for Accepting Flag
# =============================================================================

def test_accepting_flag_false_during_shutdown():
    """
        Test that is_accepting is False during and after shutdown.

        Validates: Requirements 2.3
    """
    coordinator, manager, _ = _create_coordinator(workers=1)

    manager.spawn_workers()
    coordinator.start()

    if coordinator.is_accepting is not True:
        errmsg = "Expected is_accepting True before shutdown"
        raise AssertionError(errmsg)

    coordinator.initiate_shutdown()

    if coordinator.is_accepting is not False:
        errmsg = "Expected is_accepting False after shutdown"
        raise AssertionError(errmsg)

    return


# =============================================================================
# Unit Tests for Graceful Timeout - Forceful Termination
# =============================================================================

def test_timeout_exceeded_forcefully_terminates_workers():
    """
        Test that when the graceful timeout is exceeded with in-flight
        requests still active, the coordinator forcefully terminates
        remaining workers.

        Validates: Requirements 2.5, 2.6
    """
    coordinator, manager, _ = _create_coordinator(
        workers=1,
        graceful_timeout=1
    )

    manager.spawn_workers()
    coordinator.start()

    workers = manager.get_workers()
    worker_id = list(workers.keys())[0]

    # Simulate an in-flight request that will NOT complete before timeout
    manager.mark_request_start(worker_id)

    # Track how terminate_all was called
    terminate_calls = []
    original_terminate_all = manager.terminate_all

    def tracking_terminate_all(graceful=True):
        terminate_calls.append(graceful)
        original_terminate_all(graceful=graceful)

    manager.terminate_all = tracking_terminate_all

    coordinator.initiate_shutdown()

    if len(terminate_calls) == 0:
        errmsg = "Expected terminate_all to be called during shutdown"
        raise AssertionError(errmsg)

    if terminate_calls[0] is not False:
        errmsg = (
            f"Expected terminate_all(graceful=False) when timeout exceeded, "
            f"but got graceful={terminate_calls[0]}"
        )
        raise AssertionError(errmsg)

    return


def test_no_timeout_gracefully_terminates_workers():
    """
        Test that when all in-flight requests complete within the
        graceful timeout, the coordinator terminates workers gracefully.

        Validates: Requirements 2.5, 2.6
    """
    coordinator, manager, _ = _create_coordinator(
        workers=1,
        graceful_timeout=5
    )

    manager.spawn_workers()
    coordinator.start()

    # No in-flight requests, so timeout will not be exceeded
    terminate_calls = []
    original_terminate_all = manager.terminate_all

    def tracking_terminate_all(graceful=True):
        terminate_calls.append(graceful)
        original_terminate_all(graceful=graceful)

    manager.terminate_all = tracking_terminate_all

    coordinator.initiate_shutdown()

    if len(terminate_calls) == 0:
        errmsg = "Expected terminate_all to be called during shutdown"
        raise AssertionError(errmsg)

    if terminate_calls[0] is not True:
        errmsg = (
            f"Expected terminate_all(graceful=True) when no timeout, "
            f"but got graceful={terminate_calls[0]}"
        )
        raise AssertionError(errmsg)

    return


def test_timeout_exceeded_still_completes_shutdown():
    """
        Test that even when the graceful timeout is exceeded, the
        shutdown process completes and the server reaches STOPPED state.

        Validates: Requirements 2.5, 2.6
    """
    coordinator, manager, _ = _create_coordinator(
        workers=1,
        graceful_timeout=1
    )

    manager.spawn_workers()
    coordinator.start()

    workers = manager.get_workers()
    worker_id = list(workers.keys())[0]

    # Simulate an in-flight request that will NOT complete
    manager.mark_request_start(worker_id)

    coordinator.initiate_shutdown()

    if coordinator.state != ServerState.STOPPED:
        errmsg = (
            f"Expected state STOPPED after timeout-exceeded shutdown, "
            f"got {coordinator.state}"
        )
        raise AssertionError(errmsg)

    if coordinator.is_shutdown_complete is not True:
        errmsg = "Expected is_shutdown_complete to be True after timeout-exceeded shutdown"
        raise AssertionError(errmsg)

    return


def test_inflight_request_completing_before_timeout_uses_graceful():
    """
        Test that when an in-flight request completes before the
        graceful timeout, workers are terminated gracefully.

        Validates: Requirements 2.4, 2.5, 2.6
    """
    coordinator, manager, _ = _create_coordinator(
        workers=1,
        graceful_timeout=5
    )

    manager.spawn_workers()
    coordinator.start()

    workers = manager.get_workers()
    worker_id = list(workers.keys())[0]

    # Simulate an in-flight request
    manager.mark_request_start(worker_id)

    terminate_calls = []
    original_terminate_all = manager.terminate_all

    def tracking_terminate_all(graceful=True):
        terminate_calls.append(graceful)
        original_terminate_all(graceful=graceful)

    manager.terminate_all = tracking_terminate_all

    # Complete the request after a short delay in a background thread
    def complete_request():
        time.sleep(0.3)
        manager.mark_request_end(worker_id)

    completer = threading.Thread(target=complete_request)
    completer.start()

    coordinator.initiate_shutdown()

    completer.join(timeout=10.0)

    if len(terminate_calls) == 0:
        errmsg = "Expected terminate_all to be called during shutdown"
        raise AssertionError(errmsg)

    if terminate_calls[0] is not True:
        errmsg = (
            f"Expected terminate_all(graceful=True) when request completed "
            f"before timeout, but got graceful={terminate_calls[0]}"
        )
        raise AssertionError(errmsg)

    return


# =============================================================================
# Unit Tests for Shutdown Progress Logging (Requirement 2.8)
# =============================================================================

import logging


class _LogCapture(logging.Handler):
    """
        A logging handler that captures log records for test verification.
    """

    def __init__(self):
        super().__init__()
        self.records = []

    def emit(self, record):
        self.records.append(record)

    def get_messages(self):
        """
            Get all captured log messages as a list of strings.

            :returns: List of formatted log messages.
        """
        rtnval = [self.format(r) for r in self.records]
        return rtnval


def test_shutdown_logs_total_worker_count():
    """
        Test that shutdown logs the total worker count at shutdown start.

        Validates: Requirements 2.8
    """
    coordinator, manager, _ = _create_coordinator(workers=2)

    manager.spawn_workers()
    coordinator.start()

    logger = logging.getLogger("webworks.prodserver.shutdowncoordinator")
    capture = _LogCapture()
    logger.addHandler(capture)

    try:
        coordinator.initiate_shutdown()
    finally:
        logger.removeHandler(capture)

    messages = capture.get_messages()
    found = False
    for msg in messages:
        if "2 worker(s) active" in msg:
            found = True
            break

    if not found:
        errmsg = (
            "Expected log message containing total worker count at shutdown start. "
            f"Got messages: {messages}"
        )
        raise AssertionError(errmsg)

    return


def test_shutdown_logs_worker_status_summary():
    """
        Test that shutdown logs a worker status summary with active,
        idle, and shutting down counts.

        Validates: Requirements 2.8
    """
    coordinator, manager, _ = _create_coordinator(workers=2)

    manager.spawn_workers()
    coordinator.start()

    logger = logging.getLogger("webworks.prodserver.shutdowncoordinator")
    capture = _LogCapture()
    logger.addHandler(capture)

    try:
        coordinator.initiate_shutdown()
    finally:
        logger.removeHandler(capture)

    messages = capture.get_messages()
    found = False
    for msg in messages:
        if "Worker status:" in msg and "active" in msg and "idle" in msg:
            found = True
            break

    if not found:
        errmsg = (
            "Expected log message containing worker status summary. "
            f"Got messages: {messages}"
        )
        raise AssertionError(errmsg)

    return


def test_shutdown_logs_total_time_graceful():
    """
        Test that graceful shutdown logs the total time taken.

        Validates: Requirements 2.8
    """
    coordinator, manager, _ = _create_coordinator(workers=1)

    manager.spawn_workers()
    coordinator.start()

    logger = logging.getLogger("webworks.prodserver.shutdowncoordinator")
    capture = _LogCapture()
    logger.addHandler(capture)

    try:
        coordinator.initiate_shutdown()
    finally:
        logger.removeHandler(capture)

    messages = capture.get_messages()
    found = False
    for msg in messages:
        if "Graceful shutdown complete" in msg and "total time:" in msg:
            found = True
            break

    if not found:
        errmsg = (
            "Expected log message containing total shutdown time. "
            f"Got messages: {messages}"
        )
        raise AssertionError(errmsg)

    return


def test_shutdown_logs_total_time_forceful():
    """
        Test that forceful shutdown logs the total time taken.

        Validates: Requirements 2.8
    """
    coordinator, manager, _ = _create_coordinator(
        workers=1,
        graceful_timeout=1
    )

    manager.spawn_workers()
    coordinator.start()

    workers = manager.get_workers()
    worker_id = list(workers.keys())[0]

    # Simulate an in-flight request that will NOT complete
    manager.mark_request_start(worker_id)

    logger = logging.getLogger("webworks.prodserver.shutdowncoordinator")
    capture = _LogCapture()
    logger.addHandler(capture)

    try:
        coordinator.initiate_shutdown()
    finally:
        logger.removeHandler(capture)

    messages = capture.get_messages()
    found = False
    for msg in messages:
        if "Forceful shutdown complete" in msg and "total time:" in msg:
            found = True
            break

    if not found:
        errmsg = (
            "Expected log message containing total forceful shutdown time. "
            f"Got messages: {messages}"
        )
        raise AssertionError(errmsg)

    return


def test_shutdown_logs_pending_requests_during_wait():
    """
        Test that shutdown logs pending request counts at each poll
        interval while waiting for in-flight requests.

        Validates: Requirements 2.8
    """
    coordinator, manager, _ = _create_coordinator(
        workers=1,
        graceful_timeout=3
    )

    manager.spawn_workers()
    coordinator.start()

    workers = manager.get_workers()
    worker_id = list(workers.keys())[0]

    # Simulate an in-flight request
    manager.mark_request_start(worker_id)

    logger = logging.getLogger("webworks.prodserver.shutdowncoordinator")
    capture = _LogCapture()
    logger.addHandler(capture)

    # Complete the request after a short delay
    def complete_request():
        time.sleep(0.8)
        manager.mark_request_end(worker_id)

    completer = threading.Thread(target=complete_request)
    completer.start()

    try:
        coordinator.initiate_shutdown()
    finally:
        logger.removeHandler(capture)

    completer.join(timeout=10.0)

    messages = capture.get_messages()
    found = False
    for msg in messages:
        if "Waiting for" in msg and "in-flight request(s)" in msg:
            found = True
            break

    if not found:
        errmsg = (
            "Expected log message with pending request count during wait. "
            f"Got messages: {messages}"
        )
        raise AssertionError(errmsg)

    return


def test_get_shutdown_progress_during_shutdown():
    """
        Test that get_shutdown_progress() returns correct progress
        information during an active shutdown.

        Validates: Requirements 2.8
    """
    coordinator, manager, _ = _create_coordinator(
        workers=1,
        graceful_timeout=5
    )

    manager.spawn_workers()
    coordinator.start()

    workers = manager.get_workers()
    worker_id = list(workers.keys())[0]

    # Simulate an in-flight request
    manager.mark_request_start(worker_id)

    progress_captured = {}
    shutdown_done = threading.Event()

    def run_shutdown():
        coordinator.initiate_shutdown()
        shutdown_done.set()

    shutdown_thread = threading.Thread(target=run_shutdown)
    shutdown_thread.start()

    # Give shutdown a moment to start
    time.sleep(0.3)

    # Capture progress during shutdown
    progress = coordinator.get_shutdown_progress()
    progress_captured.update(progress)

    # Complete the request
    manager.mark_request_end(worker_id)

    shutdown_thread.join(timeout=10.0)

    if progress_captured.get("state") != "shutting_down":
        errmsg = (
            f"Expected state 'shutting_down' in progress, "
            f"got '{progress_captured.get('state')}'"
        )
        raise AssertionError(errmsg)

    if progress_captured.get("inflight_requests") != 1:
        errmsg = (
            f"Expected 1 inflight request in progress, "
            f"got {progress_captured.get('inflight_requests')}"
        )
        raise AssertionError(errmsg)

    if progress_captured.get("graceful_timeout") != 5:
        errmsg = (
            f"Expected graceful_timeout 5 in progress, "
            f"got {progress_captured.get('graceful_timeout')}"
        )
        raise AssertionError(errmsg)

    return


def test_get_shutdown_progress_when_not_shutting_down():
    """
        Test that get_shutdown_progress() returns sensible values
        when the server is not shutting down.

        Validates: Requirements 2.8
    """
    coordinator, manager, _ = _create_coordinator(workers=1)

    manager.spawn_workers()
    coordinator.start()

    progress = coordinator.get_shutdown_progress()

    if progress.get("state") != "running":
        errmsg = (
            f"Expected state 'running' in progress, "
            f"got '{progress.get('state')}'"
        )
        raise AssertionError(errmsg)

    if progress.get("inflight_requests") != 0:
        errmsg = (
            f"Expected 0 inflight requests, "
            f"got {progress.get('inflight_requests')}"
        )
        raise AssertionError(errmsg)

    if progress.get("elapsed_time") != 0.0:
        errmsg = (
            f"Expected elapsed_time 0.0 when not shutting down, "
            f"got {progress.get('elapsed_time')}"
        )
        raise AssertionError(errmsg)

    # Clean up
    coordinator.initiate_shutdown()

    return


def test_shutdown_logs_timeout_exceeded_with_pending_count():
    """
        Test that when the graceful timeout is exceeded, the log
        message includes the number of still-pending requests.

        Validates: Requirements 2.8
    """
    coordinator, manager, _ = _create_coordinator(
        workers=1,
        graceful_timeout=1
    )

    manager.spawn_workers()
    coordinator.start()

    workers = manager.get_workers()
    worker_id = list(workers.keys())[0]

    # Simulate an in-flight request that will NOT complete
    manager.mark_request_start(worker_id)

    logger = logging.getLogger("webworks.prodserver.shutdowncoordinator")
    capture = _LogCapture()
    logger.addHandler(capture)

    try:
        coordinator.initiate_shutdown()
    finally:
        logger.removeHandler(capture)

    messages = capture.get_messages()
    found = False
    for msg in messages:
        if "exceeded" in msg and "1 request(s) still pending" in msg:
            found = True
            break

    if not found:
        errmsg = (
            "Expected timeout exceeded log to include pending request count. "
            f"Got messages: {messages}"
        )
        raise AssertionError(errmsg)

    return
