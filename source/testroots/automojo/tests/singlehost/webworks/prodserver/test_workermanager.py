"""
    Tests for the WorkerManager class.

    This module contains unit tests for the production server WorkerManager
    including worker spawning, termination, restart, request counting,
    max-requests recycling, timeout handling, and monitoring.
"""

from automojo.webworks.prodserver.serverconfig import ServerConfig
from automojo.webworks.prodserver.workermanager import WorkerManager, WORKER_CLASSES
from automojo.webworks.prodserver.workerstate import WorkerState, WorkerStatus
from automojo.webworks.prodserver.syncworker import SyncWorker
from automojo.webworks.prodserver.asyncworker import AsyncWorker


# =============================================================================
# Helpers
# =============================================================================

def _dummy_app(request):
    """
        Dummy application callable for testing.
    """
    return None


def _create_manager(workers: int = 2, **kwargs) -> WorkerManager:
    """
        Create a WorkerManager instance for testing.

        :param workers: Number of workers to configure.

        :returns: A WorkerManager instance.
    """
    config = ServerConfig(workers=workers, **kwargs)
    manager = WorkerManager(config=config, app=_dummy_app)

    return manager


# =============================================================================
# Unit Tests for WorkerManager Initialization
# =============================================================================

def test_workermanager_initial_worker_count_zero():
    """
        Test that a new WorkerManager has no active workers.
    """
    manager = _create_manager(workers=4)

    if manager.get_worker_count() != 0:
        errmsg = f"Expected 0 workers initially, got {manager.get_worker_count()}"
        raise AssertionError(errmsg)

    return


def test_workermanager_num_workers_from_config():
    """
        Test that num_workers reflects the configured value.
    """
    manager = _create_manager(workers=6)

    if manager.num_workers != 6:
        errmsg = f"Expected num_workers=6, got {manager.num_workers}"
        raise AssertionError(errmsg)

    return


def test_workermanager_min_workers_default():
    """
        Test that min_workers defaults to 1.
    """
    manager = _create_manager(workers=4)

    if manager.min_workers != 1:
        errmsg = f"Expected min_workers=1, got {manager.min_workers}"
        raise AssertionError(errmsg)

    return


# =============================================================================
# Unit Tests for Worker Spawning
# =============================================================================

def test_spawn_workers_creates_correct_count():
    """
        Test that spawn_workers creates the configured number of workers.
    """
    manager = _create_manager(workers=3)

    manager.spawn_workers()

    if manager.get_worker_count() != 3:
        errmsg = f"Expected 3 workers after spawn, got {manager.get_worker_count()}"
        raise AssertionError(errmsg)

    manager.terminate_all(graceful=False)

    return


def test_spawn_worker_returns_worker_instance():
    """
        Test that spawn_worker returns a Worker instance.
    """
    manager = _create_manager(workers=1)

    worker = manager.spawn_worker()

    if not isinstance(worker, SyncWorker):
        errmsg = f"Expected SyncWorker instance, got {type(worker).__name__}"
        raise AssertionError(errmsg)

    manager.terminate_all(graceful=False)

    return


def test_spawn_worker_with_async_class():
    """
        Test that spawn_worker creates AsyncWorker when configured.
    """
    manager = _create_manager(workers=1, worker_class="async")

    worker = manager.spawn_worker()

    if not isinstance(worker, AsyncWorker):
        errmsg = f"Expected AsyncWorker instance, got {type(worker).__name__}"
        raise AssertionError(errmsg)

    manager.terminate_all(graceful=False)

    return


def test_spawn_worker_assigns_unique_ids():
    """
        Test that spawned workers get unique IDs.
    """
    manager = _create_manager(workers=3)

    manager.spawn_workers()

    workers = manager.get_workers()
    ids = list(workers.keys())

    if len(ids) != len(set(ids)):
        errmsg = f"Expected unique worker IDs, got {ids}"
        raise AssertionError(errmsg)

    manager.terminate_all(graceful=False)

    return


def test_spawn_worker_sets_active_state():
    """
        Test that spawned workers are in ACTIVE state.
    """
    manager = _create_manager(workers=2)

    manager.spawn_workers()

    for worker_id, worker in manager.get_workers().items():
        if worker.state != WorkerState.ACTIVE:
            errmsg = (
                f"Expected worker {worker_id} to be ACTIVE, "
                f"got {worker.state}"
            )
            raise AssertionError(errmsg)

    manager.terminate_all(graceful=False)

    return


# =============================================================================
# Unit Tests for Worker Termination
# =============================================================================

def test_terminate_worker_removes_from_manager():
    """
        Test that terminate_worker removes the worker from the manager.
    """
    manager = _create_manager(workers=2)

    manager.spawn_workers()

    workers = manager.get_workers()
    first_id = list(workers.keys())[0]

    manager.terminate_worker(first_id)

    if first_id in manager.get_workers():
        errmsg = f"Expected worker {first_id} to be removed after termination"
        raise AssertionError(errmsg)

    manager.terminate_all(graceful=False)

    return


def test_terminate_worker_unknown_id_no_error():
    """
        Test that terminating an unknown worker ID does not raise.
    """
    manager = _create_manager(workers=1)

    # Should not raise
    manager.terminate_worker(9999)

    return


def test_terminate_all_removes_all_workers():
    """
        Test that terminate_all removes all workers.
    """
    manager = _create_manager(workers=4)

    manager.spawn_workers()
    manager.terminate_all(graceful=False)

    if manager.get_worker_count() != 0:
        errmsg = f"Expected 0 workers after terminate_all, got {manager.get_worker_count()}"
        raise AssertionError(errmsg)

    return


# =============================================================================
# Unit Tests for Worker Restart
# =============================================================================

def test_restart_worker_creates_replacement():
    """
        Test that restart_worker creates a new worker after terminating the old one.
    """
    manager = _create_manager(workers=2)

    manager.spawn_workers()

    workers_before = set(manager.get_workers().keys())
    first_id = list(workers_before)[0]

    new_worker = manager.restart_worker(first_id)

    if first_id in manager.get_workers():
        errmsg = f"Expected old worker {first_id} to be removed after restart"
        raise AssertionError(errmsg)

    if new_worker.worker_id not in manager.get_workers():
        errmsg = f"Expected new worker {new_worker.worker_id} to be in manager"
        raise AssertionError(errmsg)

    manager.terminate_all(graceful=False)

    return


# =============================================================================
# Unit Tests for Request Counting and Max-Requests
# =============================================================================

def test_increment_request_count_tracks_count():
    """
        Test that increment_request_count tracks the count correctly.
    """
    manager = _create_manager(workers=1)

    worker = manager.spawn_worker()
    wid = worker.worker_id

    manager.increment_request_count(wid)
    manager.increment_request_count(wid)

    # The worker itself should have been incremented via the manager
    # Check the internal tracking
    if manager._request_counts.get(wid) != 2:
        errmsg = f"Expected request count 2, got {manager._request_counts.get(wid)}"
        raise AssertionError(errmsg)

    manager.terminate_all(graceful=False)

    return


def test_max_requests_triggers_restart():
    """
        Test that exceeding max_requests triggers a worker restart.
    """
    manager = _create_manager(workers=1, max_requests=3, max_requests_jitter=0)

    manager.spawn_workers()

    workers = manager.get_workers()
    original_id = list(workers.keys())[0]

    # Increment up to the limit
    manager.increment_request_count(original_id)
    manager.increment_request_count(original_id)
    manager.increment_request_count(original_id)

    # The original worker should have been restarted
    if original_id in manager.get_workers():
        errmsg = (
            f"Expected worker {original_id} to be restarted after "
            f"reaching max_requests"
        )
        raise AssertionError(errmsg)

    # A new worker should exist
    if manager.get_worker_count() < 1:
        errmsg = "Expected at least 1 worker after max-requests restart"
        raise AssertionError(errmsg)

    manager.terminate_all(graceful=False)

    return


def test_max_requests_none_no_restart():
    """
        Test that workers are not restarted when max_requests is None.
    """
    manager = _create_manager(workers=1, max_requests=None)

    manager.spawn_workers()

    workers = manager.get_workers()
    original_id = list(workers.keys())[0]

    for _ in range(100):
        manager.increment_request_count(original_id)

    # Worker should still be the same
    if original_id not in manager.get_workers():
        errmsg = f"Expected worker {original_id} to still exist with no max_requests"
        raise AssertionError(errmsg)

    manager.terminate_all(graceful=False)

    return


# =============================================================================
# Unit Tests for Timeout Handling
# =============================================================================

def test_check_timeouts_no_active_requests():
    """
        Test that check_timeouts does nothing when no requests are active.
    """
    manager = _create_manager(workers=2, timeout=30)

    manager.spawn_workers()

    initial_count = manager.get_worker_count()

    # No requests started, so no timeouts
    manager.check_timeouts()

    if manager.get_worker_count() != initial_count:
        errmsg = (
            f"Expected {initial_count} workers after check_timeouts "
            f"with no active requests, got {manager.get_worker_count()}"
        )
        raise AssertionError(errmsg)

    manager.terminate_all(graceful=False)

    return


def test_mark_request_start_and_end():
    """
        Test that mark_request_start and mark_request_end track correctly.
    """
    manager = _create_manager(workers=1)

    worker = manager.spawn_worker()
    wid = worker.worker_id

    manager.mark_request_start(wid)

    if manager._request_start_times.get(wid) is None:
        errmsg = "Expected request start time to be set"
        raise AssertionError(errmsg)

    manager.mark_request_end(wid)

    if manager._request_start_times.get(wid) is not None:
        errmsg = "Expected request start time to be cleared after end"
        raise AssertionError(errmsg)

    manager.terminate_all(graceful=False)

    return


# =============================================================================
# Unit Tests for Worker Status
# =============================================================================

def test_get_worker_status_returns_all_workers():
    """
        Test that get_worker_status returns status for all workers.
    """
    manager = _create_manager(workers=3)

    manager.spawn_workers()

    statuses = manager.get_worker_status()

    if len(statuses) != 3:
        errmsg = f"Expected 3 worker statuses, got {len(statuses)}"
        raise AssertionError(errmsg)

    for worker_id, status in statuses.items():
        if not isinstance(status, WorkerStatus):
            errmsg = f"Expected WorkerStatus, got {type(status).__name__}"
            raise AssertionError(errmsg)

    manager.terminate_all(graceful=False)

    return


# =============================================================================
# Unit Tests for Worker Class Registry
# =============================================================================

def test_worker_classes_registry_contains_sync():
    """
        Test that WORKER_CLASSES contains the sync worker.
    """
    if "sync" not in WORKER_CLASSES:
        errmsg = "Expected 'sync' in WORKER_CLASSES"
        raise AssertionError(errmsg)

    return


def test_worker_classes_registry_contains_async():
    """
        Test that WORKER_CLASSES contains the async worker.
    """
    if "async" not in WORKER_CLASSES:
        errmsg = "Expected 'async' in WORKER_CLASSES"
        raise AssertionError(errmsg)

    return


def test_worker_classes_registry_contains_gevent():
    """
        Test that WORKER_CLASSES contains the gevent worker.
    """
    if "gevent" not in WORKER_CLASSES:
        errmsg = "Expected 'gevent' in WORKER_CLASSES"
        raise AssertionError(errmsg)

    return


def test_resolve_unknown_worker_class_raises():
    """
        Test that an unknown worker class raises ValueError.
    """
    manager = _create_manager(workers=1, worker_class="sync")

    # Temporarily override the config
    manager._config = ServerConfig(workers=1, worker_class="unknown")

    exception_raised = False

    try:
        manager.spawn_worker()
    except ValueError as err:
        exception_raised = True
        if "unknown" not in str(err).lower():
            errmsg = f"Expected 'unknown' in error message, got '{err}'"
            raise AssertionError(errmsg)

    if exception_raised is not True:
        errmsg = "Expected ValueError for unknown worker class"
        raise AssertionError(errmsg)

    return


# =============================================================================
# Unit Tests for Health Check
# =============================================================================

def test_check_worker_health_restarts_stopped_workers():
    """
        Test that _check_worker_health restarts workers in STOPPED state.
    """
    manager = _create_manager(workers=2)

    manager.spawn_workers()

    # Simulate a crash
    workers = manager.get_workers()
    crash_id = list(workers.keys())[0]
    workers[crash_id].mark_stopped()

    manager._check_worker_health()

    # The crashed worker should have been replaced
    if crash_id in manager.get_workers():
        errmsg = f"Expected crashed worker {crash_id} to be replaced"
        raise AssertionError(errmsg)

    # Total active count should be maintained
    active = manager.get_worker_count()
    if active < manager.min_workers:
        errmsg = (
            f"Expected at least {manager.min_workers} active workers, "
            f"got {active}"
        )
        raise AssertionError(errmsg)

    manager.terminate_all(graceful=False)

    return
