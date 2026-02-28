"""
    Tests for the abstract Worker base class.

    This module contains unit tests for the production server Worker
    abstract base class including state management, request counting,
    and status reporting.
"""

from automojo.webworks.prodserver.worker import Worker
from automojo.webworks.prodserver.workerstate import WorkerState, WorkerStatus
from automojo.webworks.prodserver.serverconfig import ServerConfig


class ConcreteWorker(Worker):
    """
        Concrete implementation of Worker for testing purposes.
    """

    def run(self) -> None:
        """
            No-op run implementation for testing.
        """
        return

    def handle_request(self, request):
        """
            No-op handle_request implementation for testing.
        """
        return None


def _create_test_worker(worker_id: int = 1) -> ConcreteWorker:
    """
        Create a ConcreteWorker instance for testing.

        :param worker_id: The worker ID to assign.

        :returns: A ConcreteWorker instance.
    """
    config = ServerConfig()
    app = object()
    worker = ConcreteWorker(worker_id=worker_id, app=app, config=config)

    return worker


# =============================================================================
# Unit Tests for Worker Initialization
# =============================================================================

def test_worker_initial_state_is_idle():
    """
        Test that a new worker starts in the IDLE state.
    """
    worker = _create_test_worker()

    if worker.state != WorkerState.IDLE:
        errmsg = f"Expected initial state IDLE, got {worker.state}"
        raise AssertionError(errmsg)

    return


def test_worker_initial_request_count_is_zero():
    """
        Test that a new worker starts with zero request count.
    """
    worker = _create_test_worker()

    if worker.request_count != 0:
        errmsg = f"Expected initial request_count 0, got {worker.request_count}"
        raise AssertionError(errmsg)

    return


def test_worker_stores_worker_id():
    """
        Test that the worker stores the assigned worker_id.
    """
    worker = _create_test_worker(worker_id=7)

    if worker.worker_id != 7:
        errmsg = f"Expected worker_id 7, got {worker.worker_id}"
        raise AssertionError(errmsg)

    return


def test_worker_stores_app():
    """
        Test that the worker stores the application reference.
    """
    config = ServerConfig()
    app = object()
    worker = ConcreteWorker(worker_id=1, app=app, config=config)

    if worker.app is not app:
        errmsg = "Expected worker.app to be the same object as the provided app"
        raise AssertionError(errmsg)

    return


def test_worker_stores_config():
    """
        Test that the worker stores the server configuration.
    """
    config = ServerConfig(port=9090)
    app = object()
    worker = ConcreteWorker(worker_id=1, app=app, config=config)

    if worker.config is not config:
        errmsg = "Expected worker.config to be the same object as the provided config"
        raise AssertionError(errmsg)

    return


def test_worker_initial_pid_is_zero():
    """
        Test that a new worker starts with pid of zero.
    """
    worker = _create_test_worker()

    if worker.pid != 0:
        errmsg = f"Expected initial pid 0, got {worker.pid}"
        raise AssertionError(errmsg)

    return


def test_worker_initial_start_time_is_zero():
    """
        Test that a new worker starts with start_time of zero.
    """
    worker = _create_test_worker()

    if worker.start_time != 0.0:
        errmsg = f"Expected initial start_time 0.0, got {worker.start_time}"
        raise AssertionError(errmsg)

    return


# =============================================================================
# Unit Tests for Worker State Transitions
# =============================================================================

def test_worker_mark_active_sets_state():
    """
        Test that mark_active transitions the worker to ACTIVE state.
    """
    worker = _create_test_worker()

    worker.mark_active()

    if worker.state != WorkerState.ACTIVE:
        errmsg = f"Expected state ACTIVE after mark_active, got {worker.state}"
        raise AssertionError(errmsg)

    return


def test_worker_mark_active_sets_start_time():
    """
        Test that mark_active sets a non-zero start_time.
    """
    worker = _create_test_worker()

    worker.mark_active()

    if worker.start_time <= 0.0:
        errmsg = f"Expected start_time > 0 after mark_active, got {worker.start_time}"
        raise AssertionError(errmsg)

    return


def test_worker_mark_stopped_sets_state():
    """
        Test that mark_stopped transitions the worker to STOPPED state.
    """
    worker = _create_test_worker()

    worker.mark_stopped()

    if worker.state != WorkerState.STOPPED:
        errmsg = f"Expected state STOPPED after mark_stopped, got {worker.state}"
        raise AssertionError(errmsg)

    return


def test_worker_shutdown_sets_shutting_down_state():
    """
        Test that shutdown transitions the worker to SHUTTING_DOWN state.
    """
    worker = _create_test_worker()

    worker.shutdown(graceful=True)

    if worker.state != WorkerState.SHUTTING_DOWN:
        errmsg = f"Expected state SHUTTING_DOWN after shutdown, got {worker.state}"
        raise AssertionError(errmsg)

    return


# =============================================================================
# Unit Tests for Worker Request Counting
# =============================================================================

def test_worker_increment_request_count():
    """
        Test that increment_request_count increases the count by one.
    """
    worker = _create_test_worker()

    worker.increment_request_count()

    if worker.request_count != 1:
        errmsg = f"Expected request_count 1 after one increment, got {worker.request_count}"
        raise AssertionError(errmsg)

    return


def test_worker_increment_request_count_multiple():
    """
        Test that multiple increments accumulate correctly.
    """
    worker = _create_test_worker()

    for _ in range(5):
        worker.increment_request_count()

    if worker.request_count != 5:
        errmsg = f"Expected request_count 5 after five increments, got {worker.request_count}"
        raise AssertionError(errmsg)

    return


# =============================================================================
# Unit Tests for Worker Status Reporting
# =============================================================================

def test_worker_get_status_returns_workerstatus():
    """
        Test that get_status returns a WorkerStatus instance.
    """
    worker = _create_test_worker()

    status = worker.get_status()

    if not isinstance(status, WorkerStatus):
        errmsg = f"Expected WorkerStatus instance, got {type(status).__name__}"
        raise AssertionError(errmsg)

    return


def test_worker_get_status_contains_worker_id():
    """
        Test that get_status includes the correct worker_id.
    """
    worker = _create_test_worker(worker_id=3)

    status = worker.get_status()

    if status.worker_id != 3:
        errmsg = f"Expected status worker_id 3, got {status.worker_id}"
        raise AssertionError(errmsg)

    return


def test_worker_get_status_contains_state():
    """
        Test that get_status includes the current state.
    """
    worker = _create_test_worker()
    worker.mark_active()

    status = worker.get_status()

    if status.state != WorkerState.ACTIVE:
        errmsg = f"Expected status state ACTIVE, got {status.state}"
        raise AssertionError(errmsg)

    return


def test_worker_get_status_contains_request_count():
    """
        Test that get_status includes the current request count.
    """
    worker = _create_test_worker()
    worker.increment_request_count()
    worker.increment_request_count()

    status = worker.get_status()

    if status.request_count != 2:
        errmsg = f"Expected status request_count 2, got {status.request_count}"
        raise AssertionError(errmsg)

    return


def test_worker_get_status_uptime_zero_when_not_started():
    """
        Test that get_status reports zero uptime when worker has not started.
    """
    worker = _create_test_worker()

    status = worker.get_status()

    if status.uptime != 0.0:
        errmsg = f"Expected uptime 0.0 when not started, got {status.uptime}"
        raise AssertionError(errmsg)

    return


def test_worker_get_status_uptime_positive_when_active():
    """
        Test that get_status reports positive uptime when worker is active.
    """
    worker = _create_test_worker()
    worker.mark_active()

    status = worker.get_status()

    if status.uptime < 0.0:
        errmsg = f"Expected non-negative uptime when active, got {status.uptime}"
        raise AssertionError(errmsg)

    return


# =============================================================================
# Unit Tests for Worker Abstract Interface
# =============================================================================

def test_worker_cannot_be_instantiated_directly():
    """
        Test that Worker cannot be instantiated directly due to abstract methods.
    """
    config = ServerConfig()
    app = object()

    try:
        Worker(worker_id=1, app=app, config=config)
        errmsg = "Expected TypeError when instantiating abstract Worker"
        raise AssertionError(errmsg)
    except TypeError:
        pass

    return
