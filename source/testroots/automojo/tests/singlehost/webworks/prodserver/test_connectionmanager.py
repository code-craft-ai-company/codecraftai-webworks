"""
    Tests for the production server ConnectionManager class.

    This module contains unit tests for connection management functionality
    including connection tracking, max connections enforcement, connection
    draining, keep-alive management, request size validation, and backlog
    configuration.
"""

import time

from automojo.webworks.prodserver.connectionmanager import (
    Connection,
    ConnectionManager,
    ConnectionState,
    RequestValidationError,
)
from automojo.webworks.prodserver.serverconfig import ServerConfig


# =============================================================================
# Unit Tests for Connection and ConnectionState
# =============================================================================

def test_connection_state_has_four_members():
    """
        Test that ConnectionState enum has the expected members.
    """
    members = list(ConnectionState)

    if len(members) != 4:
        errmsg = f"Expected 4 ConnectionState members, got {len(members)}"
        raise AssertionError(errmsg)

    return


def test_connection_state_values():
    """
        Test that ConnectionState enum values are correct.
    """
    if ConnectionState.ACTIVE.value != "active":
        errmsg = f"Expected 'active', got '{ConnectionState.ACTIVE.value}'"
        raise AssertionError(errmsg)

    if ConnectionState.IDLE.value != "idle":
        errmsg = f"Expected 'idle', got '{ConnectionState.IDLE.value}'"
        raise AssertionError(errmsg)

    if ConnectionState.DRAINING.value != "draining":
        errmsg = f"Expected 'draining', got '{ConnectionState.DRAINING.value}'"
        raise AssertionError(errmsg)

    if ConnectionState.CLOSED.value != "closed":
        errmsg = f"Expected 'closed', got '{ConnectionState.CLOSED.value}'"
        raise AssertionError(errmsg)

    return



def test_connection_default_state_is_active():
    """
        Test that a new Connection defaults to ACTIVE state.
    """
    now = time.time()
    conn = Connection(
        conn_id="conn-1",
        created_at=now,
        last_activity=now,
    )

    if conn.state != ConnectionState.ACTIVE:
        errmsg = f"Expected ACTIVE state, got {conn.state}"
        raise AssertionError(errmsg)

    return


def test_connection_default_keep_alive_is_true():
    """
        Test that a new Connection defaults to keep_alive True.
    """
    now = time.time()
    conn = Connection(
        conn_id="conn-1",
        created_at=now,
        last_activity=now,
    )

    if conn.keep_alive is not True:
        errmsg = f"Expected keep_alive True, got {conn.keep_alive}"
        raise AssertionError(errmsg)

    return


def test_connection_as_dict_contains_all_fields():
    """
        Test that Connection.as_dict returns all expected fields.
    """
    now = time.time()
    conn = Connection(
        conn_id="conn-1",
        created_at=now,
        last_activity=now,
        keep_alive=True,
        requests_handled=5,
        state=ConnectionState.IDLE,
    )

    result = conn.as_dict()

    expected_keys = {"conn_id", "created_at", "last_activity", "keep_alive", "requests_handled", "state"}
    actual_keys = set(result.keys())

    if actual_keys != expected_keys:
        errmsg = f"Expected keys {expected_keys}, got {actual_keys}"
        raise AssertionError(errmsg)

    if result["conn_id"] != "conn-1":
        errmsg = f"Expected conn_id 'conn-1', got '{result['conn_id']}'"
        raise AssertionError(errmsg)

    if result["state"] != "idle":
        errmsg = f"Expected state 'idle', got '{result['state']}'"
        raise AssertionError(errmsg)

    if result["requests_handled"] != 5:
        errmsg = f"Expected requests_handled 5, got {result['requests_handled']}"
        raise AssertionError(errmsg)

    return


# =============================================================================
# Unit Tests for RequestValidationError
# =============================================================================

def test_request_validation_error_stores_status_code():
    """
        Test that RequestValidationError stores the status code.
    """
    err = RequestValidationError(status_code=414, message="Too long")

    if err.status_code != 414:
        errmsg = f"Expected status_code 414, got {err.status_code}"
        raise AssertionError(errmsg)

    return


def test_request_validation_error_stores_message():
    """
        Test that RequestValidationError stores the message.
    """
    err = RequestValidationError(status_code=431, message="Too many headers")

    if str(err) != "Too many headers":
        errmsg = f"Expected message 'Too many headers', got '{str(err)}'"
        raise AssertionError(errmsg)

    return


# =============================================================================
# Unit Tests for ConnectionManager - Accept and Close
# =============================================================================

def test_accept_connection_increments_count():
    """
        Test that accepting a connection increments the connection count.
    """
    config = ServerConfig()
    manager = ConnectionManager(config=config)

    accepted = manager.accept_connection(conn_id="conn-1")

    if accepted is not True:
        errmsg = "Expected connection to be accepted"
        raise AssertionError(errmsg)

    if manager.connection_count != 1:
        errmsg = f"Expected connection_count 1, got {manager.connection_count}"
        raise AssertionError(errmsg)

    return


def test_accept_multiple_connections():
    """
        Test that multiple connections can be accepted and tracked.
    """
    config = ServerConfig()
    manager = ConnectionManager(config=config)

    manager.accept_connection(conn_id="conn-1")
    manager.accept_connection(conn_id="conn-2")
    manager.accept_connection(conn_id="conn-3")

    if manager.connection_count != 3:
        errmsg = f"Expected connection_count 3, got {manager.connection_count}"
        raise AssertionError(errmsg)

    return


def test_close_connection_decrements_count():
    """
        Test that closing a connection decrements the connection count.
    """
    config = ServerConfig()
    manager = ConnectionManager(config=config)

    manager.accept_connection(conn_id="conn-1")
    manager.accept_connection(conn_id="conn-2")
    manager.close_connection(conn_id="conn-1")

    if manager.connection_count != 1:
        errmsg = f"Expected connection_count 1, got {manager.connection_count}"
        raise AssertionError(errmsg)

    return


def test_close_nonexistent_connection_is_safe():
    """
        Test that closing a nonexistent connection does not raise.
    """
    config = ServerConfig()
    manager = ConnectionManager(config=config)

    manager.close_connection(conn_id="nonexistent")

    if manager.connection_count != 0:
        errmsg = f"Expected connection_count 0, got {manager.connection_count}"
        raise AssertionError(errmsg)

    return


def test_get_connection_returns_tracked_connection():
    """
        Test that get_connection returns a tracked connection.
    """
    config = ServerConfig()
    manager = ConnectionManager(config=config)

    manager.accept_connection(conn_id="conn-1")
    conn = manager.get_connection(conn_id="conn-1")

    if conn is None:
        errmsg = "Expected connection to be found"
        raise AssertionError(errmsg)

    if conn.conn_id != "conn-1":
        errmsg = f"Expected conn_id 'conn-1', got '{conn.conn_id}'"
        raise AssertionError(errmsg)

    return


def test_get_connection_returns_none_for_unknown():
    """
        Test that get_connection returns None for unknown connection ID.
    """
    config = ServerConfig()
    manager = ConnectionManager(config=config)

    conn = manager.get_connection(conn_id="unknown")

    if conn is not None:
        errmsg = "Expected None for unknown connection"
        raise AssertionError(errmsg)

    return



# =============================================================================
# Unit Tests for ConnectionManager - Max Connections Enforcement
# =============================================================================

def test_max_connections_rejects_when_limit_reached():
    """
        Test that connections are rejected when max_connections is reached.
    """
    config = ServerConfig(max_connections=2)
    manager = ConnectionManager(config=config)

    result_1 = manager.accept_connection(conn_id="conn-1")
    result_2 = manager.accept_connection(conn_id="conn-2")
    result_3 = manager.accept_connection(conn_id="conn-3")

    if result_1 is not True:
        errmsg = "Expected first connection to be accepted"
        raise AssertionError(errmsg)

    if result_2 is not True:
        errmsg = "Expected second connection to be accepted"
        raise AssertionError(errmsg)

    if result_3 is not False:
        errmsg = "Expected third connection to be rejected"
        raise AssertionError(errmsg)

    if manager.connection_count != 2:
        errmsg = f"Expected connection_count 2, got {manager.connection_count}"
        raise AssertionError(errmsg)

    return


def test_max_connections_allows_after_close():
    """
        Test that new connections are accepted after closing one at the limit.
    """
    config = ServerConfig(max_connections=2)
    manager = ConnectionManager(config=config)

    manager.accept_connection(conn_id="conn-1")
    manager.accept_connection(conn_id="conn-2")
    manager.close_connection(conn_id="conn-1")

    result = manager.accept_connection(conn_id="conn-3")

    if result is not True:
        errmsg = "Expected connection to be accepted after closing one"
        raise AssertionError(errmsg)

    if manager.connection_count != 2:
        errmsg = f"Expected connection_count 2, got {manager.connection_count}"
        raise AssertionError(errmsg)

    return


def test_no_max_connections_allows_unlimited():
    """
        Test that connections are unlimited when max_connections is None.
    """
    config = ServerConfig(max_connections=None)
    manager = ConnectionManager(config=config)

    for i in range(100):
        result = manager.accept_connection(conn_id=f"conn-{i}")
        if result is not True:
            errmsg = f"Expected connection conn-{i} to be accepted"
            raise AssertionError(errmsg)

    if manager.connection_count != 100:
        errmsg = f"Expected connection_count 100, got {manager.connection_count}"
        raise AssertionError(errmsg)

    return


def test_max_connections_property():
    """
        Test that the max_connections property returns the configured value.
    """
    config = ServerConfig(max_connections=50)
    manager = ConnectionManager(config=config)

    if manager.max_connections != 50:
        errmsg = f"Expected max_connections 50, got {manager.max_connections}"
        raise AssertionError(errmsg)

    return


# =============================================================================
# Unit Tests for ConnectionManager - Connection Activity
# =============================================================================

def test_record_activity_updates_timestamp():
    """
        Test that record_activity updates the last_activity timestamp.
    """
    config = ServerConfig()
    manager = ConnectionManager(config=config)

    manager.accept_connection(conn_id="conn-1")
    conn_before = manager.get_connection(conn_id="conn-1")
    original_activity = conn_before.last_activity

    time.sleep(0.01)
    manager.record_activity(conn_id="conn-1")

    conn_after = manager.get_connection(conn_id="conn-1")

    if conn_after.last_activity <= original_activity:
        errmsg = "Expected last_activity to be updated"
        raise AssertionError(errmsg)

    return


def test_record_activity_increments_requests_handled():
    """
        Test that record_activity increments the requests_handled counter.
    """
    config = ServerConfig()
    manager = ConnectionManager(config=config)

    manager.accept_connection(conn_id="conn-1")
    manager.record_activity(conn_id="conn-1")
    manager.record_activity(conn_id="conn-1")

    conn = manager.get_connection(conn_id="conn-1")

    if conn.requests_handled != 2:
        errmsg = f"Expected requests_handled 2, got {conn.requests_handled}"
        raise AssertionError(errmsg)

    return


def test_mark_idle_sets_idle_state():
    """
        Test that mark_idle transitions a connection to IDLE state.
    """
    config = ServerConfig()
    manager = ConnectionManager(config=config)

    manager.accept_connection(conn_id="conn-1")
    manager.mark_idle(conn_id="conn-1")

    conn = manager.get_connection(conn_id="conn-1")

    if conn.state != ConnectionState.IDLE:
        errmsg = f"Expected IDLE state, got {conn.state}"
        raise AssertionError(errmsg)

    return


def test_record_activity_sets_active_state():
    """
        Test that record_activity transitions a connection back to ACTIVE.
    """
    config = ServerConfig()
    manager = ConnectionManager(config=config)

    manager.accept_connection(conn_id="conn-1")
    manager.mark_idle(conn_id="conn-1")
    manager.record_activity(conn_id="conn-1")

    conn = manager.get_connection(conn_id="conn-1")

    if conn.state != ConnectionState.ACTIVE:
        errmsg = f"Expected ACTIVE state, got {conn.state}"
        raise AssertionError(errmsg)

    return



# =============================================================================
# Unit Tests for ConnectionManager - Connection Draining
# =============================================================================

def test_close_idle_connections_closes_idle_keep_alive():
    """
        Test that close_idle_connections closes idle keep-alive connections.
    """
    config = ServerConfig()
    manager = ConnectionManager(config=config)

    manager.accept_connection(conn_id="conn-1")
    manager.accept_connection(conn_id="conn-2")
    manager.accept_connection(conn_id="conn-3")

    manager.mark_idle(conn_id="conn-1")
    manager.mark_idle(conn_id="conn-3")

    closed = manager.close_idle_connections()

    if closed != 2:
        errmsg = f"Expected 2 connections closed, got {closed}"
        raise AssertionError(errmsg)

    if manager.connection_count != 1:
        errmsg = f"Expected connection_count 1, got {manager.connection_count}"
        raise AssertionError(errmsg)

    return


def test_close_idle_connections_keeps_active():
    """
        Test that close_idle_connections does not close active connections.
    """
    config = ServerConfig()
    manager = ConnectionManager(config=config)

    manager.accept_connection(conn_id="conn-1")
    manager.accept_connection(conn_id="conn-2")

    closed = manager.close_idle_connections()

    if closed != 0:
        errmsg = f"Expected 0 connections closed, got {closed}"
        raise AssertionError(errmsg)

    if manager.connection_count != 2:
        errmsg = f"Expected connection_count 2, got {manager.connection_count}"
        raise AssertionError(errmsg)

    return


def test_drain_connections_rejects_new_connections():
    """
        Test that draining mode rejects new connections.
    """
    config = ServerConfig()
    manager = ConnectionManager(config=config)

    manager.accept_connection(conn_id="conn-1")
    manager.mark_idle(conn_id="conn-1")

    manager.drain_connections(timeout=0.5)

    result = manager.accept_connection(conn_id="conn-2")

    if result is not False:
        errmsg = "Expected connection to be rejected during draining"
        raise AssertionError(errmsg)

    return


def test_drain_connections_returns_true_when_all_drained():
    """
        Test that drain_connections returns True when all connections close.
    """
    config = ServerConfig()
    manager = ConnectionManager(config=config)

    manager.accept_connection(conn_id="conn-1")
    manager.mark_idle(conn_id="conn-1")

    result = manager.drain_connections(timeout=1.0)

    if result is not True:
        errmsg = "Expected drain to succeed"
        raise AssertionError(errmsg)

    if manager.connection_count != 0:
        errmsg = f"Expected connection_count 0, got {manager.connection_count}"
        raise AssertionError(errmsg)

    return


def test_drain_connections_returns_false_on_timeout():
    """
        Test that drain_connections returns False when timeout is exceeded.
    """
    config = ServerConfig()
    manager = ConnectionManager(config=config)

    manager.accept_connection(conn_id="conn-1")
    # conn-1 stays ACTIVE, so it won't be closed by drain

    result = manager.drain_connections(timeout=0.3)

    if result is not False:
        errmsg = "Expected drain to timeout"
        raise AssertionError(errmsg)

    return


def test_is_draining_property():
    """
        Test that is_draining reflects the draining state.
    """
    config = ServerConfig()
    manager = ConnectionManager(config=config)

    if manager.is_draining is not False:
        errmsg = "Expected is_draining to be False initially"
        raise AssertionError(errmsg)

    manager.drain_connections(timeout=0.1)

    if manager.is_draining is not True:
        errmsg = "Expected is_draining to be True after draining"
        raise AssertionError(errmsg)

    return


# =============================================================================
# Unit Tests for ConnectionManager - Request Size Limits
# =============================================================================

def test_validate_request_line_passes_within_limit():
    """
        Test that validate_request_line passes for lines within the limit.
    """
    config = ServerConfig(limit_request_line=100)
    manager = ConnectionManager(config=config)

    request_line = "GET /index.html HTTP/1.1"
    manager.validate_request_line(request_line=request_line)

    return


def test_validate_request_line_raises_when_exceeded():
    """
        Test that validate_request_line raises when the limit is exceeded.
    """
    config = ServerConfig(limit_request_line=10)
    manager = ConnectionManager(config=config)

    request_line = "GET /very/long/path/that/exceeds/the/limit HTTP/1.1"

    raised = False
    status_code = None

    try:
        manager.validate_request_line(request_line=request_line)
    except RequestValidationError as err:
        raised = True
        status_code = err.status_code

    if raised is not True:
        errmsg = "Expected RequestValidationError to be raised"
        raise AssertionError(errmsg)

    if status_code != 414:
        errmsg = f"Expected status_code 414, got {status_code}"
        raise AssertionError(errmsg)

    return


def test_validate_request_line_allows_zero_limit():
    """
        Test that validate_request_line allows any length when limit is 0.
    """
    config = ServerConfig(limit_request_line=0)
    manager = ConnectionManager(config=config)

    long_line = "GET /" + "a" * 10000 + " HTTP/1.1"
    manager.validate_request_line(request_line=long_line)

    return


def test_validate_request_headers_passes_within_limit():
    """
        Test that validate_request_headers passes when within the limit.
    """
    config = ServerConfig(limit_request_fields=100)
    manager = ConnectionManager(config=config)

    manager.validate_request_headers(header_count=50)

    return


def test_validate_request_headers_raises_when_exceeded():
    """
        Test that validate_request_headers raises when the limit is exceeded.
    """
    config = ServerConfig(limit_request_fields=10)
    manager = ConnectionManager(config=config)

    raised = False
    status_code = None

    try:
        manager.validate_request_headers(header_count=15)
    except RequestValidationError as err:
        raised = True
        status_code = err.status_code

    if raised is not True:
        errmsg = "Expected RequestValidationError to be raised"
        raise AssertionError(errmsg)

    if status_code != 431:
        errmsg = f"Expected status_code 431, got {status_code}"
        raise AssertionError(errmsg)

    return


def test_validate_request_headers_allows_zero_limit():
    """
        Test that validate_request_headers allows any count when limit is 0.
    """
    config = ServerConfig(limit_request_fields=0)
    manager = ConnectionManager(config=config)

    manager.validate_request_headers(header_count=500)

    return


def test_validate_request_line_at_exact_limit():
    """
        Test that validate_request_line passes at exactly the limit.
    """
    config = ServerConfig(limit_request_line=20)
    manager = ConnectionManager(config=config)

    request_line = "a" * 20
    manager.validate_request_line(request_line=request_line)

    return


def test_validate_request_headers_at_exact_limit():
    """
        Test that validate_request_headers passes at exactly the limit.
    """
    config = ServerConfig(limit_request_fields=50)
    manager = ConnectionManager(config=config)

    manager.validate_request_headers(header_count=50)

    return



# =============================================================================
# Unit Tests for ConnectionManager - Backlog and Keep-Alive Configuration
# =============================================================================

def test_backlog_property_returns_configured_value():
    """
        Test that the backlog property returns the configured backlog.
    """
    config = ServerConfig(backlog=1024)
    manager = ConnectionManager(config=config)

    if manager.backlog != 1024:
        errmsg = f"Expected backlog 1024, got {manager.backlog}"
        raise AssertionError(errmsg)

    return


def test_backlog_property_returns_default():
    """
        Test that the backlog property returns the default value.
    """
    config = ServerConfig()
    manager = ConnectionManager(config=config)

    if manager.backlog != 2048:
        errmsg = f"Expected default backlog 2048, got {manager.backlog}"
        raise AssertionError(errmsg)

    return


def test_keep_alive_timeout_property_returns_configured_value():
    """
        Test that the keep_alive_timeout property returns the configured value.
    """
    config = ServerConfig(keep_alive=30)
    manager = ConnectionManager(config=config)

    if manager.keep_alive_timeout != 30:
        errmsg = f"Expected keep_alive_timeout 30, got {manager.keep_alive_timeout}"
        raise AssertionError(errmsg)

    return


def test_keep_alive_timeout_property_returns_default():
    """
        Test that the keep_alive_timeout property returns the default value.
    """
    config = ServerConfig()
    manager = ConnectionManager(config=config)

    if manager.keep_alive_timeout != 5:
        errmsg = f"Expected default keep_alive_timeout 5, got {manager.keep_alive_timeout}"
        raise AssertionError(errmsg)

    return


def test_close_expired_keep_alive_connections():
    """
        Test that expired keep-alive connections are closed.
    """
    config = ServerConfig(keep_alive=0)
    manager = ConnectionManager(config=config)

    manager.accept_connection(conn_id="conn-1")
    manager.mark_idle(conn_id="conn-1")

    time.sleep(0.05)

    closed = manager.close_expired_keep_alive_connections()

    if closed != 1:
        errmsg = f"Expected 1 expired connection closed, got {closed}"
        raise AssertionError(errmsg)

    return


def test_close_expired_keep_alive_keeps_recent():
    """
        Test that recently active keep-alive connections are not closed.
    """
    config = ServerConfig(keep_alive=60)
    manager = ConnectionManager(config=config)

    manager.accept_connection(conn_id="conn-1")
    manager.mark_idle(conn_id="conn-1")

    closed = manager.close_expired_keep_alive_connections()

    if closed != 0:
        errmsg = f"Expected 0 connections closed, got {closed}"
        raise AssertionError(errmsg)

    return


# =============================================================================
# Unit Tests for ConnectionManager - Status and Reset
# =============================================================================

def test_get_status_returns_expected_fields():
    """
        Test that get_status returns all expected fields.
    """
    config = ServerConfig(max_connections=100, backlog=512, keep_alive=10)
    manager = ConnectionManager(config=config)

    manager.accept_connection(conn_id="conn-1")
    manager.accept_connection(conn_id="conn-2")
    manager.mark_idle(conn_id="conn-2")

    status = manager.get_status()

    expected_keys = {
        "total_connections", "active_connections", "idle_connections",
        "draining_connections", "max_connections", "backlog",
        "keep_alive_timeout", "is_draining",
    }
    actual_keys = set(status.keys())

    if actual_keys != expected_keys:
        errmsg = f"Expected keys {expected_keys}, got {actual_keys}"
        raise AssertionError(errmsg)

    if status["total_connections"] != 2:
        errmsg = f"Expected total_connections 2, got {status['total_connections']}"
        raise AssertionError(errmsg)

    if status["active_connections"] != 1:
        errmsg = f"Expected active_connections 1, got {status['active_connections']}"
        raise AssertionError(errmsg)

    if status["idle_connections"] != 1:
        errmsg = f"Expected idle_connections 1, got {status['idle_connections']}"
        raise AssertionError(errmsg)

    if status["max_connections"] != 100:
        errmsg = f"Expected max_connections 100, got {status['max_connections']}"
        raise AssertionError(errmsg)

    if status["backlog"] != 512:
        errmsg = f"Expected backlog 512, got {status['backlog']}"
        raise AssertionError(errmsg)

    if status["keep_alive_timeout"] != 10:
        errmsg = f"Expected keep_alive_timeout 10, got {status['keep_alive_timeout']}"
        raise AssertionError(errmsg)

    return


def test_get_all_connections_returns_snapshot():
    """
        Test that get_all_connections returns all tracked connections.
    """
    config = ServerConfig()
    manager = ConnectionManager(config=config)

    manager.accept_connection(conn_id="conn-1")
    manager.accept_connection(conn_id="conn-2")

    all_conns = manager.get_all_connections()

    if len(all_conns) != 2:
        errmsg = f"Expected 2 connections, got {len(all_conns)}"
        raise AssertionError(errmsg)

    if "conn-1" not in all_conns:
        errmsg = "Expected 'conn-1' in connections"
        raise AssertionError(errmsg)

    if "conn-2" not in all_conns:
        errmsg = "Expected 'conn-2' in connections"
        raise AssertionError(errmsg)

    return


def test_reset_clears_all_state():
    """
        Test that reset clears all connections and resets draining.
    """
    config = ServerConfig()
    manager = ConnectionManager(config=config)

    manager.accept_connection(conn_id="conn-1")
    manager.accept_connection(conn_id="conn-2")
    manager.drain_connections(timeout=0.1)

    manager.reset()

    if manager.connection_count != 0:
        errmsg = f"Expected connection_count 0, got {manager.connection_count}"
        raise AssertionError(errmsg)

    if manager.is_draining is not False:
        errmsg = "Expected is_draining to be False after reset"
        raise AssertionError(errmsg)

    return


def test_get_connection_count_method():
    """
        Test that get_connection_count returns the correct count.
    """
    config = ServerConfig()
    manager = ConnectionManager(config=config)

    manager.accept_connection(conn_id="conn-1")
    manager.accept_connection(conn_id="conn-2")

    count = manager.get_connection_count()

    if count != 2:
        errmsg = f"Expected count 2, got {count}"
        raise AssertionError(errmsg)

    return
