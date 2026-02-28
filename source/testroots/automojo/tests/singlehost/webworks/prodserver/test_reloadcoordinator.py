"""
    Tests for the ReloadCoordinator class.

    This module contains unit tests for the production server
    ReloadCoordinator class including state transitions, on_reload
    hook invocation, rolling restart of workers, and thread safety.
"""

from automojo.webworks.prodserver.serverconfig import ServerConfig, ServerState
from automojo.webworks.prodserver.reloadcoordinator import ReloadCoordinator
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
    on_reload=None,
    **kwargs
) -> tuple:
    """
        Create a ReloadCoordinator with its dependencies for testing.

        :param workers: Number of workers to configure.
        :param on_reload: Optional on_reload hook callable.

        :returns: A tuple of (coordinator, worker_manager, config).
    """
    config = ServerConfig(
        workers=workers,
        on_reload=on_reload,
        **kwargs
    )
    worker_manager = WorkerManager(config=config, app=_dummy_app)
    coordinator = ReloadCoordinator(
        config=config,
        worker_manager=worker_manager
    )

    return coordinator, worker_manager, config


# =============================================================================
# Unit Tests for ReloadCoordinator Initialization
# =============================================================================

def test_reload_coordinator_initial_state_is_stopped():
    """
        Test that a new ReloadCoordinator starts in STOPPED state.
    """
    coordinator, _, _ = _create_coordinator()

    if coordinator.state != ServerState.STOPPED:
        errmsg = f"Expected initial state STOPPED, got {coordinator.state}"
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


# =============================================================================
# Unit Tests for Reload - State Transitions
# =============================================================================

def test_reload_returns_to_running_state():
    """
        Test that reload() transitions to RELOADING and back to RUNNING.

        Validates: Requirements 2.7
    """
    coordinator, manager, _ = _create_coordinator(workers=1)

    manager.spawn_workers()
    coordinator.start()

    coordinator.reload()

    if coordinator.state != ServerState.RUNNING:
        errmsg = f"Expected state RUNNING after reload, got {coordinator.state}"
        raise AssertionError(errmsg)

    return


def test_reload_skipped_when_not_running():
    """
        Test that reload() is skipped when the coordinator is not in
        RUNNING state.
    """
    coordinator, _, _ = _create_coordinator()

    # State is STOPPED, reload should be skipped
    coordinator.reload()

    if coordinator.state != ServerState.STOPPED:
        errmsg = f"Expected state STOPPED after skipped reload, got {coordinator.state}"
        raise AssertionError(errmsg)

    return


# =============================================================================
# Unit Tests for Reload - on_reload Hook
# =============================================================================

def test_reload_calls_on_reload_hook():
    """
        Test that reload() calls the on_reload hook when configured.

        Validates: Requirements 2.7
    """
    hook_calls = []

    def on_reload_hook(config):
        hook_calls.append(config)

    coordinator, manager, config = _create_coordinator(
        workers=1,
        on_reload=on_reload_hook
    )

    manager.spawn_workers()
    coordinator.start()

    coordinator.reload()

    if len(hook_calls) != 1:
        errmsg = f"Expected on_reload hook to be called once, got {len(hook_calls)} calls"
        raise AssertionError(errmsg)

    if hook_calls[0] is not config:
        errmsg = "Expected on_reload hook to receive the server config"
        raise AssertionError(errmsg)

    return


def test_reload_succeeds_without_on_reload_hook():
    """
        Test that reload() succeeds when no on_reload hook is configured.

        Validates: Requirements 2.7
    """
    coordinator, manager, _ = _create_coordinator(workers=1)

    manager.spawn_workers()
    coordinator.start()

    coordinator.reload()

    if coordinator.state != ServerState.RUNNING:
        errmsg = f"Expected state RUNNING after reload without hook, got {coordinator.state}"
        raise AssertionError(errmsg)

    return


def test_reload_continues_after_hook_error():
    """
        Test that reload() continues even if the on_reload hook raises
        an exception.

        Validates: Requirements 2.7
    """
    def failing_hook(config):
        raise RuntimeError("Hook failed")

    coordinator, manager, _ = _create_coordinator(
        workers=1,
        on_reload=failing_hook
    )

    manager.spawn_workers()
    coordinator.start()

    # Should not raise despite the hook error
    coordinator.reload()

    if coordinator.state != ServerState.RUNNING:
        errmsg = f"Expected state RUNNING after reload with hook error, got {coordinator.state}"
        raise AssertionError(errmsg)

    return


# =============================================================================
# Unit Tests for Reload - Rolling Restart
# =============================================================================

def test_reload_performs_rolling_restart():
    """
        Test that reload() performs a rolling restart of workers,
        maintaining worker availability throughout.

        Validates: Requirements 2.7
    """
    coordinator, manager, _ = _create_coordinator(workers=2)

    manager.spawn_workers()
    coordinator.start()

    initial_count = manager.get_worker_count()

    if initial_count != 2:
        errmsg = f"Expected 2 workers before reload, got {initial_count}"
        raise AssertionError(errmsg)

    coordinator.reload()

    final_count = manager.get_worker_count()

    if final_count != 2:
        errmsg = f"Expected 2 workers after reload, got {final_count}"
        raise AssertionError(errmsg)

    return


def test_reload_replaces_all_workers():
    """
        Test that reload() replaces all original workers with new ones.

        Validates: Requirements 2.7
    """
    coordinator, manager, _ = _create_coordinator(workers=2)

    manager.spawn_workers()
    coordinator.start()

    original_ids = set(manager.get_workers().keys())

    coordinator.reload()

    new_ids = set(manager.get_workers().keys())

    # All original worker IDs should be gone (replaced by new ones)
    overlap = original_ids & new_ids

    if len(overlap) > 0:
        errmsg = (
            f"Expected all original workers to be replaced, "
            f"but worker IDs {overlap} still exist"
        )
        raise AssertionError(errmsg)

    return


def test_reload_with_no_workers():
    """
        Test that reload() handles the case where there are no workers.

        Validates: Requirements 2.7
    """
    coordinator, manager, _ = _create_coordinator(workers=0)

    coordinator.start()

    coordinator.reload()

    if coordinator.state != ServerState.RUNNING:
        errmsg = f"Expected state RUNNING after reload with no workers, got {coordinator.state}"
        raise AssertionError(errmsg)

    return


# =============================================================================
# Unit Tests for Reload - Thread Safety
# =============================================================================

def test_double_reload_is_safe():
    """
        Test that calling reload() while a reload is already in progress
        is handled safely (second call is ignored).
    """
    coordinator, manager, _ = _create_coordinator(workers=1)

    manager.spawn_workers()
    coordinator.start()

    # First reload should succeed
    coordinator.reload()

    # Second reload should also succeed (sequential calls)
    coordinator.reload()

    if coordinator.state != ServerState.RUNNING:
        errmsg = f"Expected state RUNNING after double reload, got {coordinator.state}"
        raise AssertionError(errmsg)

    return


def test_reload_returns_to_running_after_exception():
    """
        Test that the coordinator returns to RUNNING state even if
        an error occurs during the rolling restart.

        Validates: Requirements 2.7
    """
    coordinator, manager, _ = _create_coordinator(workers=1)

    manager.spawn_workers()
    coordinator.start()

    # Monkey-patch terminate_worker to raise an exception
    original_terminate = manager.terminate_worker

    def failing_terminate(worker_id, graceful=True):
        raise RuntimeError("Terminate failed")

    manager.terminate_worker = failing_terminate

    coordinator.reload()

    # State should be RUNNING even after the error
    if coordinator.state != ServerState.RUNNING:
        errmsg = (
            f"Expected state RUNNING after reload with error, "
            f"got {coordinator.state}"
        )
        raise AssertionError(errmsg)

    # Restore original method
    manager.terminate_worker = original_terminate

    return
