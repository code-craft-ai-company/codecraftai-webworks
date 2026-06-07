"""
    Tests for the WorkerState enum and WorkerStatus dataclass.

    This module contains unit tests for the worker state and status
    types used by the production server worker management system.
"""

from ccai.webworks.prodserver.workerstate import WorkerState, WorkerStatus


# =============================================================================
# Unit Tests for WorkerState Enum
# =============================================================================

def test_workerstate_idle_value():
    """
        Test that WorkerState.IDLE has the correct value.
    """
    expected = "idle"
    if WorkerState.IDLE.value != expected:
        errmsg = f"Expected WorkerState.IDLE value '{expected}', got '{WorkerState.IDLE.value}'"
        raise AssertionError(errmsg)

    return


def test_workerstate_active_value():
    """
        Test that WorkerState.ACTIVE has the correct value.
    """
    expected = "active"
    if WorkerState.ACTIVE.value != expected:
        errmsg = f"Expected WorkerState.ACTIVE value '{expected}', got '{WorkerState.ACTIVE.value}'"
        raise AssertionError(errmsg)

    return


def test_workerstate_shutting_down_value():
    """
        Test that WorkerState.SHUTTING_DOWN has the correct value.
    """
    expected = "shutting_down"
    if WorkerState.SHUTTING_DOWN.value != expected:
        errmsg = f"Expected WorkerState.SHUTTING_DOWN value '{expected}', got '{WorkerState.SHUTTING_DOWN.value}'"
        raise AssertionError(errmsg)

    return


def test_workerstate_stopped_value():
    """
        Test that WorkerState.STOPPED has the correct value.
    """
    expected = "stopped"
    if WorkerState.STOPPED.value != expected:
        errmsg = f"Expected WorkerState.STOPPED value '{expected}', got '{WorkerState.STOPPED.value}'"
        raise AssertionError(errmsg)

    return


def test_workerstate_has_four_members():
    """
        Test that WorkerState has exactly four members.
    """
    member_count = len(WorkerState)
    expected = 4
    if member_count != expected:
        errmsg = f"Expected {expected} WorkerState members, got {member_count}"
        raise AssertionError(errmsg)

    return


# =============================================================================
# Unit Tests for WorkerStatus Dataclass
# =============================================================================

def test_workerstatus_stores_worker_id():
    """
        Test that WorkerStatus stores the worker_id correctly.
    """
    status = WorkerStatus(
        worker_id=5,
        pid=1234,
        state=WorkerState.ACTIVE,
        request_count=100,
        memory_usage=50000,
        uptime=120.5,
    )

    if status.worker_id != 5:
        errmsg = f"Expected worker_id 5, got {status.worker_id}"
        raise AssertionError(errmsg)

    return


def test_workerstatus_stores_pid():
    """
        Test that WorkerStatus stores the pid correctly.
    """
    status = WorkerStatus(
        worker_id=1,
        pid=9876,
        state=WorkerState.IDLE,
        request_count=0,
        memory_usage=0,
        uptime=0.0,
    )

    if status.pid != 9876:
        errmsg = f"Expected pid 9876, got {status.pid}"
        raise AssertionError(errmsg)

    return


def test_workerstatus_stores_state():
    """
        Test that WorkerStatus stores the state correctly.
    """
    status = WorkerStatus(
        worker_id=1,
        pid=1000,
        state=WorkerState.SHUTTING_DOWN,
        request_count=50,
        memory_usage=10000,
        uptime=60.0,
    )

    if status.state != WorkerState.SHUTTING_DOWN:
        errmsg = f"Expected state SHUTTING_DOWN, got {status.state}"
        raise AssertionError(errmsg)

    return


def test_workerstatus_stores_request_count():
    """
        Test that WorkerStatus stores the request_count correctly.
    """
    status = WorkerStatus(
        worker_id=1,
        pid=1000,
        state=WorkerState.ACTIVE,
        request_count=42,
        memory_usage=0,
        uptime=0.0,
    )

    if status.request_count != 42:
        errmsg = f"Expected request_count 42, got {status.request_count}"
        raise AssertionError(errmsg)

    return


def test_workerstatus_as_dict_contains_all_fields():
    """
        Test that WorkerStatus.as_dict returns all fields.
    """
    status = WorkerStatus(
        worker_id=3,
        pid=5555,
        state=WorkerState.ACTIVE,
        request_count=200,
        memory_usage=80000,
        uptime=300.0,
    )

    result = status.as_dict()

    expected_keys = {"worker_id", "pid", "state", "request_count", "memory_usage", "uptime"}
    actual_keys = set(result.keys())

    if actual_keys != expected_keys:
        errmsg = f"Expected keys {expected_keys}, got {actual_keys}"
        raise AssertionError(errmsg)

    return


def test_workerstatus_as_dict_serializes_state_value():
    """
        Test that WorkerStatus.as_dict serializes the state as its string value.
    """
    status = WorkerStatus(
        worker_id=1,
        pid=1000,
        state=WorkerState.ACTIVE,
        request_count=0,
        memory_usage=0,
        uptime=0.0,
    )

    result = status.as_dict()

    if result["state"] != "active":
        errmsg = f"Expected state value 'active', got '{result['state']}'"
        raise AssertionError(errmsg)

    return
