"""
    Property-Based Tests for Worker Restart on Crash (Property 2).

    Property 2: Worker Restart on Crash
    For any worker process that crashes, the WorkerManager SHALL spawn
    a replacement worker, maintaining the configured worker count.

    Validates: Requirements 1.3
"""

import random

from ccai.webworks.prodserver.serverconfig import ServerConfig
from ccai.webworks.prodserver.workermanager import WorkerManager
from ccai.webworks.prodserver.workerstate import WorkerState


# =============================================================================
# Helpers
# =============================================================================

def _dummy_app(request):
    """
        Dummy application callable for testing.
    """
    return None


def _simulate_crash(manager: WorkerManager, worker_id: int) -> None:
    """
        Simulate a worker crash by marking it as stopped.

        :param manager: The WorkerManager instance.
        :param worker_id: The ID of the worker to crash.
    """
    workers = manager.get_workers()
    if worker_id in workers:
        workers[worker_id].mark_stopped()

    return


# =============================================================================
# Random Generators
# =============================================================================

def generate_worker_count() -> int:
    """
        Generate a random worker count between 2 and 8.
    """
    return random.randint(2, 8)


def generate_crash_count(worker_count: int) -> int:
    """
        Generate a random number of workers to crash.

        :param worker_count: Total number of workers.

        :returns: Number of workers to crash (1 to worker_count - 1).
    """
    return random.randint(1, max(1, worker_count - 1))


# =============================================================================
# Property-Based Tests
# =============================================================================

# Feature: production-server, Property 2: Worker Restart on Crash
# *For any* worker process that crashes, the WorkerManager SHALL spawn
# a replacement worker, maintaining the configured worker count.
# **Validates: Requirements 1.3**


def test_property_2_crashed_worker_is_restarted():
    """
        Property 2: Single Worker Crash Recovery

        For any single crashed worker, calling _check_worker_health()
        SHALL restart the crashed worker and maintain the total worker
        count.

        **Validates: Requirement 1.3**
    """
    for iteration in range(100):
        worker_count = generate_worker_count()
        config = ServerConfig(workers=worker_count)
        manager = WorkerManager(config=config, app=_dummy_app)

        manager.spawn_workers()

        # Pick a random worker to crash
        workers = manager.get_workers()
        crash_id = random.choice(list(workers.keys()))

        _simulate_crash(manager, crash_id)

        # Verify the worker is in STOPPED state
        workers_after_crash = manager.get_workers()
        if crash_id in workers_after_crash:
            if workers_after_crash[crash_id].state != WorkerState.STOPPED:
                errmsg = (
                    f"Iteration {iteration}: crashed worker {crash_id} "
                    f"not in STOPPED state"
                )
                raise AssertionError(errmsg)

        # Run health check to trigger recovery
        manager._check_worker_health()

        # Property: total active worker count must be restored
        active_count = manager.get_worker_count()
        if active_count < worker_count:
            errmsg = (
                f"Iteration {iteration}: expected at least {worker_count} "
                f"active workers after recovery, got {active_count}"
            )
            raise AssertionError(errmsg)

        manager.terminate_all(graceful=False)

    return


def test_property_2_multiple_crashes_recovered():
    """
        Property 2: Multiple Worker Crash Recovery

        For any subset of crashed workers, calling _check_worker_health()
        SHALL restart all crashed workers and restore the worker count.

        **Validates: Requirement 1.3**
    """
    for iteration in range(100):
        worker_count = generate_worker_count()
        config = ServerConfig(workers=worker_count)
        manager = WorkerManager(config=config, app=_dummy_app)

        manager.spawn_workers()

        # Crash a random subset of workers
        workers = manager.get_workers()
        crash_count = generate_crash_count(worker_count)
        crash_ids = random.sample(list(workers.keys()), crash_count)

        for crash_id in crash_ids:
            _simulate_crash(manager, crash_id)

        # Run health check to trigger recovery
        manager._check_worker_health()

        # Property: all workers should be non-STOPPED after recovery
        active_count = manager.get_worker_count()
        if active_count < manager.min_workers:
            errmsg = (
                f"Iteration {iteration}: active workers ({active_count}) "
                f"below minimum ({manager.min_workers}) after recovering "
                f"from {crash_count} crashes"
            )
            raise AssertionError(errmsg)

        manager.terminate_all(graceful=False)

    return


def test_property_2_replacement_workers_are_active():
    """
        Property 2: Replacement Workers Are Active

        For any crashed worker that is replaced, the replacement worker
        SHALL be in the ACTIVE state after recovery.

        **Validates: Requirement 1.3**
    """
    for iteration in range(100):
        worker_count = generate_worker_count()
        config = ServerConfig(workers=worker_count)
        manager = WorkerManager(config=config, app=_dummy_app)

        manager.spawn_workers()

        # Crash one random worker
        workers = manager.get_workers()
        crash_id = random.choice(list(workers.keys()))

        _simulate_crash(manager, crash_id)

        # Run health check to trigger recovery
        manager._check_worker_health()

        # Property: all current workers should be ACTIVE
        statuses = manager.get_worker_status()
        for worker_id, status in statuses.items():
            if status.state != WorkerState.ACTIVE:
                errmsg = (
                    f"Iteration {iteration}: worker {worker_id} has state "
                    f"{status.state} after recovery, expected ACTIVE"
                )
                raise AssertionError(errmsg)

        manager.terminate_all(graceful=False)

    return
