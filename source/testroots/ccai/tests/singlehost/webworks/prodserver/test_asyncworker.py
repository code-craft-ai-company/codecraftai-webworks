"""
    Tests for the AsyncWorker class.

    This module contains unit tests for the asynchronous worker
    implementation used for ASGI applications in the production server.
"""

import asyncio

from ccai.webworks.prodserver.asyncworker import AsyncWorker
from ccai.webworks.prodserver.workerstate import WorkerState
from ccai.webworks.prodserver.serverconfig import ServerConfig


def _create_async_echo_app():
    """
        Create a simple async echo application for testing.

        :returns: An async callable that returns its input.
    """
    async def echo_app(request):
        return request

    return echo_app


def _create_test_asyncworker(worker_id: int = 1) -> AsyncWorker:
    """
        Create an AsyncWorker instance for testing.

        :param worker_id: The worker ID to assign.

        :returns: An AsyncWorker instance.
    """
    config = ServerConfig(worker_class="async")
    app = _create_async_echo_app()
    worker = AsyncWorker(worker_id=worker_id, app=app, config=config)

    return worker


# =============================================================================
# Unit Tests for AsyncWorker Initialization
# =============================================================================

def test_asyncworker_initial_state_is_idle():
    """
        Test that a new AsyncWorker starts in the IDLE state.
    """
    worker = _create_test_asyncworker()

    if worker.state != WorkerState.IDLE:
        errmsg = f"Expected initial state IDLE, got {worker.state}"
        raise AssertionError(errmsg)

    return


def test_asyncworker_initial_loop_is_none():
    """
        Test that the event loop is None before run is called.
    """
    worker = _create_test_asyncworker()

    if worker.loop is not None:
        errmsg = "Expected loop to be None before run"
        raise AssertionError(errmsg)

    return


def test_asyncworker_initial_request_count_is_zero():
    """
        Test that a new AsyncWorker starts with zero request count.
    """
    worker = _create_test_asyncworker()

    if worker.request_count != 0:
        errmsg = f"Expected initial request_count 0, got {worker.request_count}"
        raise AssertionError(errmsg)

    return


# =============================================================================
# Unit Tests for AsyncWorker Run
# =============================================================================

def test_asyncworker_run_creates_event_loop():
    """
        Test that run creates the asyncio event loop.
    """
    worker = _create_test_asyncworker()

    worker.run()

    if worker.loop is None:
        errmsg = "Expected loop to be created after run"
        raise AssertionError(errmsg)

    worker.shutdown()

    return


def test_asyncworker_run_sets_active_state():
    """
        Test that run transitions the worker to ACTIVE state.
    """
    worker = _create_test_asyncworker()

    worker.run()

    if worker.state != WorkerState.ACTIVE:
        errmsg = f"Expected state ACTIVE after run, got {worker.state}"
        raise AssertionError(errmsg)

    worker.shutdown()

    return


def test_asyncworker_run_sets_pid():
    """
        Test that run sets the worker pid.
    """
    worker = _create_test_asyncworker()

    worker.run()

    if worker.pid <= 0:
        errmsg = f"Expected positive pid after run, got {worker.pid}"
        raise AssertionError(errmsg)

    worker.shutdown()

    return


# =============================================================================
# Unit Tests for AsyncWorker Request Handling
# =============================================================================

def test_asyncworker_handle_request_returns_response():
    """
        Test that handle_request returns the application response.
    """
    worker = _create_test_asyncworker()
    worker.run()

    sentinel = object()
    response = worker.handle_request(sentinel)

    if response is not sentinel:
        errmsg = "Expected handle_request to return the echo app response"
        raise AssertionError(errmsg)

    worker.shutdown()

    return


def test_asyncworker_handle_request_increments_count():
    """
        Test that handle_request increments the request count.
    """
    worker = _create_test_asyncworker()
    worker.run()

    worker.handle_request("request1")
    worker.handle_request("request2")
    worker.handle_request("request3")

    if worker.request_count != 3:
        errmsg = f"Expected request_count 3, got {worker.request_count}"
        raise AssertionError(errmsg)

    worker.shutdown()

    return


# =============================================================================
# Unit Tests for AsyncWorker Shutdown
# =============================================================================

def test_asyncworker_shutdown_sets_stopped_state():
    """
        Test that shutdown transitions the worker to STOPPED state.
    """
    worker = _create_test_asyncworker()
    worker.run()

    worker.shutdown(graceful=True)

    if worker.state != WorkerState.STOPPED:
        errmsg = f"Expected state STOPPED after shutdown, got {worker.state}"
        raise AssertionError(errmsg)

    return


def test_asyncworker_shutdown_clears_loop():
    """
        Test that shutdown clears the event loop.
    """
    worker = _create_test_asyncworker()
    worker.run()

    worker.shutdown(graceful=True)

    if worker.loop is not None:
        errmsg = "Expected loop to be None after shutdown"
        raise AssertionError(errmsg)

    return


def test_asyncworker_shutdown_non_graceful():
    """
        Test that non-graceful shutdown also stops the worker.
    """
    worker = _create_test_asyncworker()
    worker.run()

    worker.shutdown(graceful=False)

    if worker.state != WorkerState.STOPPED:
        errmsg = f"Expected state STOPPED after non-graceful shutdown, got {worker.state}"
        raise AssertionError(errmsg)

    return
