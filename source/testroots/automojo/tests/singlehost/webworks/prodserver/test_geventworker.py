"""
    Tests for the GeventWorker class.

    This module contains unit tests for the gevent-based worker
    implementation used for cooperative multitasking in the production
    server. Tests that require gevent are skipped if gevent is not
    installed.
"""

from automojo.webworks.prodserver.geventworker import GeventWorker, _GEVENT_AVAILABLE
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


def _create_test_geventworker(worker_id: int = 1, threads: int = 4) -> GeventWorker:
    """
        Create a GeventWorker instance for testing.

        :param worker_id: The worker ID to assign.
        :param threads: Pool size for the gevent pool.

        :returns: A GeventWorker instance.
    """
    config = ServerConfig(worker_class="gevent", threads=threads)
    app = _create_echo_app()
    worker = GeventWorker(worker_id=worker_id, app=app, config=config)

    return worker


# =============================================================================
# Unit Tests for GeventWorker Initialization
# =============================================================================

def test_geventworker_initial_state_is_idle():
    """
        Test that a new GeventWorker starts in the IDLE state.
    """
    worker = _create_test_geventworker()

    if worker.state != WorkerState.IDLE:
        errmsg = f"Expected initial state IDLE, got {worker.state}"
        raise AssertionError(errmsg)

    return


def test_geventworker_initial_pool_is_none():
    """
        Test that the gevent pool is None before run is called.
    """
    worker = _create_test_geventworker()

    if worker.pool is not None:
        errmsg = "Expected pool to be None before run"
        raise AssertionError(errmsg)

    return


def test_geventworker_initial_request_count_is_zero():
    """
        Test that a new GeventWorker starts with zero request count.
    """
    worker = _create_test_geventworker()

    if worker.request_count != 0:
        errmsg = f"Expected initial request_count 0, got {worker.request_count}"
        raise AssertionError(errmsg)

    return


# =============================================================================
# Unit Tests for GeventWorker Run (gevent-dependent)
# =============================================================================

def test_geventworker_run_raises_without_gevent():
    """
        Test that run raises ImportError when gevent is not available.

        This test only runs when gevent is NOT installed.
    """
    if _GEVENT_AVAILABLE:
        # Skip this test when gevent is installed
        return

    worker = _create_test_geventworker()

    try:
        worker.run()
        errmsg = "Expected ImportError when gevent is not installed"
        raise AssertionError(errmsg)
    except ImportError:
        pass

    return


def test_geventworker_run_creates_pool_when_gevent_available():
    """
        Test that run creates the gevent pool when gevent is installed.

        This test only runs when gevent IS installed.
    """
    if not _GEVENT_AVAILABLE:
        # Skip this test when gevent is not installed
        return

    worker = _create_test_geventworker()

    worker.run()

    if worker.pool is None:
        errmsg = "Expected pool to be created after run"
        raise AssertionError(errmsg)

    worker.shutdown()

    return


def test_geventworker_run_sets_active_when_gevent_available():
    """
        Test that run transitions to ACTIVE state when gevent is installed.

        This test only runs when gevent IS installed.
    """
    if not _GEVENT_AVAILABLE:
        # Skip this test when gevent is not installed
        return

    worker = _create_test_geventworker()

    worker.run()

    if worker.state != WorkerState.ACTIVE:
        errmsg = f"Expected state ACTIVE after run, got {worker.state}"
        raise AssertionError(errmsg)

    worker.shutdown()

    return


def test_geventworker_run_sets_pid_when_gevent_available():
    """
        Test that run sets the worker pid when gevent is installed.

        This test only runs when gevent IS installed.
    """
    if not _GEVENT_AVAILABLE:
        # Skip this test when gevent is not installed
        return

    worker = _create_test_geventworker()

    worker.run()

    if worker.pid <= 0:
        errmsg = f"Expected positive pid after run, got {worker.pid}"
        raise AssertionError(errmsg)

    worker.shutdown()

    return


# =============================================================================
# Unit Tests for GeventWorker Request Handling (gevent-dependent)
# =============================================================================

def test_geventworker_handle_request_when_gevent_available():
    """
        Test that handle_request returns the application response.

        This test only runs when gevent IS installed.
    """
    if not _GEVENT_AVAILABLE:
        # Skip this test when gevent is not installed
        return

    worker = _create_test_geventworker()
    worker.run()

    sentinel = object()
    response = worker.handle_request(sentinel)

    if response is not sentinel:
        errmsg = "Expected handle_request to return the echo app response"
        raise AssertionError(errmsg)

    worker.shutdown()

    return


def test_geventworker_handle_request_increments_count_when_gevent_available():
    """
        Test that handle_request increments the request count.

        This test only runs when gevent IS installed.
    """
    if not _GEVENT_AVAILABLE:
        # Skip this test when gevent is not installed
        return

    worker = _create_test_geventworker()
    worker.run()

    worker.handle_request("request1")
    worker.handle_request("request2")

    if worker.request_count != 2:
        errmsg = f"Expected request_count 2, got {worker.request_count}"
        raise AssertionError(errmsg)

    worker.shutdown()

    return


# =============================================================================
# Unit Tests for GeventWorker Shutdown (gevent-dependent)
# =============================================================================

def test_geventworker_shutdown_sets_stopped_when_gevent_available():
    """
        Test that shutdown transitions to STOPPED state.

        This test only runs when gevent IS installed.
    """
    if not _GEVENT_AVAILABLE:
        # Skip this test when gevent is not installed
        return

    worker = _create_test_geventworker()
    worker.run()

    worker.shutdown(graceful=True)

    if worker.state != WorkerState.STOPPED:
        errmsg = f"Expected state STOPPED after shutdown, got {worker.state}"
        raise AssertionError(errmsg)

    return


def test_geventworker_shutdown_clears_pool_when_gevent_available():
    """
        Test that shutdown clears the gevent pool.

        This test only runs when gevent IS installed.
    """
    if not _GEVENT_AVAILABLE:
        # Skip this test when gevent is not installed
        return

    worker = _create_test_geventworker()
    worker.run()

    worker.shutdown(graceful=True)

    if worker.pool is not None:
        errmsg = "Expected pool to be None after shutdown"
        raise AssertionError(errmsg)

    return


# =============================================================================
# Unit Tests for GeventWorker without gevent (fallback behavior)
# =============================================================================

def test_geventworker_handle_request_without_pool():
    """
        Test that handle_request works without a pool by calling app directly.
    """
    config = ServerConfig(worker_class="gevent")
    app = _create_echo_app()
    worker = GeventWorker(worker_id=1, app=app, config=config)

    # Do not call run(), so pool is None
    sentinel = object()
    response = worker.handle_request(sentinel)

    if response is not sentinel:
        errmsg = "Expected handle_request to call app directly when pool is None"
        raise AssertionError(errmsg)

    return
