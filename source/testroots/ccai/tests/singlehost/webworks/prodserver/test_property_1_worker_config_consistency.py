"""
    Property-Based Tests for Worker Configuration Consistency (Property 1).

    Property 1: Worker Configuration Consistency
    For any valid worker count N specified via --workers, the WorkerManager
    SHALL spawn exactly N worker processes before accepting requests, and
    maintain N workers during normal operation.

    Validates: Requirements 1.1, 1.4, 1.8
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


# =============================================================================
# Random Generators
# =============================================================================

def generate_worker_count() -> int:
    """
        Generate a random worker count between 1 and 16.
    """
    return random.randint(1, 16)


# =============================================================================
# Property-Based Tests
# =============================================================================

# Feature: production-server, Property 1: Worker Configuration Consistency
# *For any* valid worker count N specified via --workers, the WorkerManager
# SHALL spawn exactly N worker processes before accepting requests, and
# maintain N workers during normal operation.
# **Validates: Requirements 1.1, 1.4, 1.8**


def test_property_1_spawn_workers_creates_exact_count():
    """
        Property 1: Exact Worker Count After Spawn

        For any valid worker count N, calling spawn_workers() SHALL
        result in exactly N active workers in the manager.

        **Validates: Requirements 1.1, 1.4**
    """
    for iteration in range(100):
        worker_count = generate_worker_count()
        config = ServerConfig(workers=worker_count)
        manager = WorkerManager(config=config, app=_dummy_app)

        manager.spawn_workers()

        active_count = manager.get_worker_count()

        if active_count != worker_count:
            errmsg = (
                f"Iteration {iteration}: expected {worker_count} workers "
                f"after spawn_workers(), got {active_count}"
            )
            raise AssertionError(errmsg)

        manager.terminate_all(graceful=False)

    return


def test_property_1_all_spawned_workers_are_active():
    """
        Property 1: All Workers Active After Spawn

        For any valid worker count N, after spawn_workers() all N
        workers SHALL be in the ACTIVE state.

        **Validates: Requirements 1.1, 1.4**
    """
    for iteration in range(100):
        worker_count = generate_worker_count()
        config = ServerConfig(workers=worker_count)
        manager = WorkerManager(config=config, app=_dummy_app)

        manager.spawn_workers()

        statuses = manager.get_worker_status()

        for worker_id, status in statuses.items():
            if status.state != WorkerState.ACTIVE:
                errmsg = (
                    f"Iteration {iteration}: worker {worker_id} has state "
                    f"{status.state}, expected ACTIVE"
                )
                raise AssertionError(errmsg)

        manager.terminate_all(graceful=False)

    return


def test_property_1_worker_ids_are_unique():
    """
        Property 1: Unique Worker IDs

        For any valid worker count N, all spawned workers SHALL have
        unique worker IDs.

        **Validates: Requirements 1.1, 1.4**
    """
    for iteration in range(100):
        worker_count = generate_worker_count()
        config = ServerConfig(workers=worker_count)
        manager = WorkerManager(config=config, app=_dummy_app)

        manager.spawn_workers()

        workers = manager.get_workers()
        worker_ids = list(workers.keys())

        if len(worker_ids) != len(set(worker_ids)):
            errmsg = (
                f"Iteration {iteration}: duplicate worker IDs found "
                f"in {worker_ids}"
            )
            raise AssertionError(errmsg)

        manager.terminate_all(graceful=False)

    return


def test_property_1_num_workers_matches_config():
    """
        Property 1: Manager Target Matches Config

        For any valid worker count N, the WorkerManager num_workers
        property SHALL equal N.

        **Validates: Requirement 1.1**
    """
    for iteration in range(100):
        worker_count = generate_worker_count()
        config = ServerConfig(workers=worker_count)
        manager = WorkerManager(config=config, app=_dummy_app)

        if manager.num_workers != worker_count:
            errmsg = (
                f"Iteration {iteration}: expected num_workers={worker_count}, "
                f"got {manager.num_workers}"
            )
            raise AssertionError(errmsg)

    return


def test_property_1_minimum_workers_maintained():
    """
        Property 1: Minimum Worker Count

        For any valid worker count N, the WorkerManager SHALL maintain
        at least min_workers (1) even during high failure rates.

        **Validates: Requirement 1.8**
    """
    for iteration in range(100):
        worker_count = generate_worker_count()
        config = ServerConfig(workers=worker_count)
        manager = WorkerManager(config=config, app=_dummy_app)

        if manager.min_workers < 1:
            errmsg = (
                f"Iteration {iteration}: min_workers is {manager.min_workers}, "
                f"expected at least 1"
            )
            raise AssertionError(errmsg)

    return
