"""
    Tests for the SyncWorker class.

    This module contains unit tests for the synchronous worker
    implementation used for WSGI applications in the production server.
"""

from automojo.webworks.prodserver.syncworker import SyncWorker
from automojo.webworks.prodserver.workerstate import WorkerState
from automojo.webworks.prodserver.serverconfig import ServerConfig


def _create_echo_app():
    """
        Create a simple echo application for testing.

        :returns: A callable that returns its input.
    """
    def echo_app(request):
        return request

    return echo_app


def _create_test_syncworker(worker_id: int = 1, threads: int = 2) -> SyncWorker:
    """
        Create a SyncWorker instance for testing.

        :param worker_id: The worker ID to assign.
        :param threads: Number of threads for the thread pool.

        :returns: A SyncWorker instance.
    """
    config = ServerConfig(threads=threads)
    app = _create_echo_app()
    worker = SyncWorker(worker_id=worker_id, app=app, config=config)

    return worker


# =============================================================================
# Unit Tests for SyncWorker Initialization
# =============================================================================

def test_syncworker_initial_state_is_idle():
    """
        Test that a new SyncWorker starts in the IDLE state.
    """
    worker = _create_test_syncworker()

    if worker.state != WorkerState.IDLE:
        errmsg = f"Expected initial state IDLE, got {worker.state}"
        raise AssertionError(errmsg)

    return


def test_syncworker_initial_thread_pool_is_none():
    """
        Test that the thread pool is None before run is called.
    """
    worker = _create_test_syncworker()

    if worker.thread_pool is not None:
        errmsg = "Expected thread_pool to be None before run"
        raise AssertionError(errmsg)

    return


def test_syncworker_initial_request_count_is_zero():
    """
        Test that a new SyncWorker starts with zero request count.
    """
    worker = _create_test_syncworker()

    if worker.request_count != 0:
        errmsg = f"Expected initial request_count 0, got {worker.request_count}"
        raise AssertionError(errmsg)

    return


# =============================================================================
# Unit Tests for SyncWorker Run
# =============================================================================

def test_syncworker_run_creates_thread_pool():
    """
        Test that run creates the thread pool.
    """
    worker = _create_test_syncworker()

    worker.run()

    if worker.thread_pool is None:
        errmsg = "Expected thread_pool to be created after run"
        raise AssertionError(errmsg)

    worker.shutdown()

    return


def test_syncworker_run_sets_active_state():
    """
        Test that run transitions the worker to ACTIVE state.
    """
    worker = _create_test_syncworker()

    worker.run()

    if worker.state != WorkerState.ACTIVE:
        errmsg = f"Expected state ACTIVE after run, got {worker.state}"
        raise AssertionError(errmsg)

    worker.shutdown()

    return


def test_syncworker_run_sets_pid():
    """
        Test that run sets the worker pid.
    """
    worker = _create_test_syncworker()

    worker.run()

    if worker.pid <= 0:
        errmsg = f"Expected positive pid after run, got {worker.pid}"
        raise AssertionError(errmsg)

    worker.shutdown()

    return


# =============================================================================
# Unit Tests for SyncWorker Request Handling
# =============================================================================

def test_syncworker_handle_request_returns_response():
    """
        Test that handle_request returns the application response.
    """
    worker = _create_test_syncworker()
    worker.run()

    sentinel = object()
    response = worker.handle_request(sentinel)

    if response is not sentinel:
        errmsg = "Expected handle_request to return the echo app response"
        raise AssertionError(errmsg)

    worker.shutdown()

    return


def test_syncworker_handle_request_increments_count():
    """
        Test that handle_request increments the request count.
    """
    worker = _create_test_syncworker()
    worker.run()

    worker.handle_request("request1")
    worker.handle_request("request2")

    if worker.request_count != 2:
        errmsg = f"Expected request_count 2, got {worker.request_count}"
        raise AssertionError(errmsg)

    worker.shutdown()

    return


# =============================================================================
# Unit Tests for SyncWorker Shutdown
# =============================================================================

def test_syncworker_shutdown_sets_stopped_state():
    """
        Test that shutdown transitions the worker to STOPPED state.
    """
    worker = _create_test_syncworker()
    worker.run()

    worker.shutdown(graceful=True)

    if worker.state != WorkerState.STOPPED:
        errmsg = f"Expected state STOPPED after shutdown, got {worker.state}"
        raise AssertionError(errmsg)

    return


def test_syncworker_shutdown_clears_thread_pool():
    """
        Test that shutdown clears the thread pool.
    """
    worker = _create_test_syncworker()
    worker.run()

    worker.shutdown(graceful=True)

    if worker.thread_pool is not None:
        errmsg = "Expected thread_pool to be None after shutdown"
        raise AssertionError(errmsg)

    return


def test_syncworker_shutdown_non_graceful():
    """
        Test that non-graceful shutdown also stops the worker.
    """
    worker = _create_test_syncworker()
    worker.run()

    worker.shutdown(graceful=False)

    if worker.state != WorkerState.STOPPED:
        errmsg = f"Expected state STOPPED after non-graceful shutdown, got {worker.state}"
        raise AssertionError(errmsg)

    return
