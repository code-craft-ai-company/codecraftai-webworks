"""
    Property-Based Tests for Graceful Shutdown Behavior (Property 3).

    Property 3: Graceful Shutdown Behavior
    For any graceful shutdown initiated by SIGTERM or SIGINT, the server
    SHALL stop accepting new connections while allowing all in-flight
    requests to complete within the graceful timeout period.

    Validates: Requirements 2.1, 2.2, 2.3, 2.4, 2.5, 2.6
"""

import random
import threading
import time

from ccai.webworks.prodserver.serverconfig import ServerConfig, ServerState
from ccai.webworks.prodserver.shutdowncoordinator import ShutdownCoordinator
from ccai.webworks.prodserver.workermanager import WorkerManager


# =============================================================================
# Helpers
# =============================================================================

def _dummy_app(request):
    """
        Dummy application callable for testing.
    """
    return None


def _create_coordinator(workers, graceful_timeout=5):
    """
        Create a ShutdownCoordinator with its dependencies for testing.

        :param workers: Number of workers to configure.
        :param graceful_timeout: Graceful shutdown timeout in seconds.

        :returns: A tuple of (coordinator, worker_manager, config).
    """
    config = ServerConfig(
        workers=workers,
        graceful_timeout=graceful_timeout
    )
    manager = WorkerManager(config=config, app=_dummy_app)
    coordinator = ShutdownCoordinator(
        config=config,
        worker_manager=manager
    )

    return coordinator, manager, config


# =============================================================================
# Random Generators
# =============================================================================

def generate_worker_count(low=1, high=8) -> int:
    """
        Generate a random worker count between low and high inclusive.
    """
    return random.randint(low, high)


def generate_graceful_timeout(low=1, high=10) -> int:
    """
        Generate a random graceful timeout between low and high inclusive.
    """
    return random.randint(low, high)


# =============================================================================
# Property-Based Tests
# =============================================================================

# Feature: production-server, Property 3: Graceful Shutdown Behavior
# *For any* graceful shutdown initiated by SIGTERM or SIGINT, the server
# SHALL stop accepting new connections while allowing all in-flight
# requests to complete within the graceful timeout period.
# **Validates: Requirements 2.1, 2.2, 2.3, 2.4, 2.5, 2.6**


def test_property_3_shutdown_stops_accepting_connections():
    """
        Property 3: Shutdown Stops Accepting Connections

        For any worker count N (1-8) and graceful timeout T (1-10),
        after initiate_shutdown(), is_accepting SHALL be False.

        **Validates: Requirements 2.3**
    """
    for iteration in range(100):
        worker_count = generate_worker_count(1, 8)
        graceful_timeout = generate_graceful_timeout(1, 10)

        coordinator, manager, _ = _create_coordinator(
            workers=worker_count,
            graceful_timeout=graceful_timeout
        )

        manager.spawn_workers()
        coordinator.start()

        if coordinator.is_accepting is not True:
            manager.terminate_all(graceful=False)
            errmsg = (
                f"Iteration {iteration}: expected is_accepting True before "
                f"shutdown (workers={worker_count}, timeout={graceful_timeout})"
            )
            raise AssertionError(errmsg)

        coordinator.initiate_shutdown()

        if coordinator.is_accepting is not False:
            errmsg = (
                f"Iteration {iteration}: expected is_accepting False after "
                f"shutdown (workers={worker_count}, timeout={graceful_timeout})"
            )
            raise AssertionError(errmsg)

    return


def test_property_3_shutdown_reaches_stopped_state():
    """
        Property 3: Shutdown Reaches STOPPED State

        For any worker count N (1-8), after initiate_shutdown(),
        state SHALL be STOPPED.

        **Validates: Requirements 2.1, 2.2**
    """
    for iteration in range(100):
        worker_count = generate_worker_count(1, 8)

        coordinator, manager, _ = _create_coordinator(
            workers=worker_count,
            graceful_timeout=5
        )

        manager.spawn_workers()
        coordinator.start()

        coordinator.initiate_shutdown()

        if coordinator.state != ServerState.STOPPED:
            errmsg = (
                f"Iteration {iteration}: expected state STOPPED after "
                f"shutdown, got {coordinator.state} (workers={worker_count})"
            )
            raise AssertionError(errmsg)

    return


def test_property_3_shutdown_terminates_all_workers():
    """
        Property 3: Shutdown Terminates All Workers

        For any worker count N (1-8), after initiate_shutdown(),
        worker count SHALL be 0.

        **Validates: Requirements 2.1, 2.2**
    """
    for iteration in range(100):
        worker_count = generate_worker_count(1, 8)

        coordinator, manager, _ = _create_coordinator(
            workers=worker_count,
            graceful_timeout=5
        )

        manager.spawn_workers()
        coordinator.start()

        coordinator.initiate_shutdown()

        remaining = manager.get_worker_count()

        if remaining != 0:
            errmsg = (
                f"Iteration {iteration}: expected 0 workers after shutdown, "
                f"got {remaining} (initial workers={worker_count})"
            )
            raise AssertionError(errmsg)

    return


def test_property_3_shutdown_marks_complete():
    """
        Property 3: Shutdown Marks Complete

        For any worker count N (1-8), after initiate_shutdown(),
        is_shutdown_complete SHALL be True.

        **Validates: Requirements 2.1, 2.2**
    """
    for iteration in range(100):
        worker_count = generate_worker_count(1, 8)

        coordinator, manager, _ = _create_coordinator(
            workers=worker_count,
            graceful_timeout=5
        )

        manager.spawn_workers()
        coordinator.start()

        coordinator.initiate_shutdown()

        if coordinator.is_shutdown_complete is not True:
            errmsg = (
                f"Iteration {iteration}: expected is_shutdown_complete True "
                f"after shutdown (workers={worker_count})"
            )
            raise AssertionError(errmsg)

    return


def test_property_3_inflight_requests_complete_before_shutdown():
    """
        Property 3: In-Flight Requests Complete Before Shutdown

        For any worker count N (1-4) with some workers having in-flight
        requests, shutdown SHALL wait for them to complete before
        terminating workers. Uses a background thread to complete
        requests shortly after shutdown begins.

        **Validates: Requirements 2.4**
    """
    for iteration in range(20):
        worker_count = generate_worker_count(1, 4)

        coordinator, manager, _ = _create_coordinator(
            workers=worker_count,
            graceful_timeout=3
        )

        manager.spawn_workers()
        coordinator.start()

        workers = manager.get_workers()
        worker_ids = list(workers.keys())

        # Pick a random subset of workers to have in-flight requests
        inflight_count = random.randint(1, len(worker_ids))
        inflight_ids = random.sample(worker_ids, inflight_count)

        for wid in inflight_ids:
            manager.mark_request_start(wid)

        # Track whether terminate_all was called gracefully
        terminate_calls = []
        original_terminate_all = manager.terminate_all

        def tracking_terminate_all(graceful=True):
            terminate_calls.append(graceful)
            original_terminate_all(graceful=graceful)

        manager.terminate_all = tracking_terminate_all

        shutdown_done = threading.Event()

        def run_shutdown():
            coordinator.initiate_shutdown()
            shutdown_done.set()

        # Complete in-flight requests after a short delay
        def complete_requests():
            time.sleep(0.3)
            for wid in inflight_ids:
                manager.mark_request_end(wid)

        completer = threading.Thread(target=complete_requests)
        completer.start()

        shutdown_thread = threading.Thread(target=run_shutdown)
        shutdown_thread.start()

        shutdown_thread.join(timeout=10.0)
        completer.join(timeout=5.0)

        if not shutdown_done.is_set():
            errmsg = (
                f"Iteration {iteration}: shutdown did not complete "
                f"(workers={worker_count}, inflight={inflight_count})"
            )
            raise AssertionError(errmsg)


        # Verify graceful termination was used (requests completed in time)
        if len(terminate_calls) == 0:
            errmsg = (
                f"Iteration {iteration}: terminate_all was not called "
                f"(workers={worker_count}, inflight={inflight_count})"
            )
            raise AssertionError(errmsg)

        if terminate_calls[0] is not True:
            errmsg = (
                f"Iteration {iteration}: expected graceful termination "
                f"when in-flight requests completed in time, got "
                f"graceful={terminate_calls[0]} "
                f"(workers={worker_count}, inflight={inflight_count})"
            )
            raise AssertionError(errmsg)

    return


def test_property_3_timeout_exceeded_forces_shutdown():
    """
        Property 3: Timeout Exceeded Forces Shutdown

        For any worker count N (1-4) with in-flight requests that
        do NOT complete, when graceful_timeout is exceeded, shutdown
        SHALL still complete with state=STOPPED and
        is_shutdown_complete=True. Uses graceful_timeout=1 so tests
        run quickly.

        **Validates: Requirements 2.5, 2.6**
    """
    for iteration in range(20):
        worker_count = generate_worker_count(1, 4)

        coordinator, manager, _ = _create_coordinator(
            workers=worker_count,
            graceful_timeout=1
        )

        manager.spawn_workers()
        coordinator.start()

        workers = manager.get_workers()
        worker_ids = list(workers.keys())

        # Pick a random subset of workers to have in-flight requests
        inflight_count = random.randint(1, len(worker_ids))
        inflight_ids = random.sample(worker_ids, inflight_count)

        for wid in inflight_ids:
            manager.mark_request_start(wid)

        # Do NOT complete the in-flight requests - let timeout expire
        coordinator.initiate_shutdown()

        if coordinator.state != ServerState.STOPPED:
            errmsg = (
                f"Iteration {iteration}: expected state STOPPED after "
                f"timeout-exceeded shutdown, got {coordinator.state} "
                f"(workers={worker_count}, inflight={inflight_count})"
            )
            raise AssertionError(errmsg)

        if coordinator.is_shutdown_complete is not True:
            errmsg = (
                f"Iteration {iteration}: expected is_shutdown_complete "
                f"True after timeout-exceeded shutdown "
                f"(workers={worker_count}, inflight={inflight_count})"
            )
            raise AssertionError(errmsg)

    return
