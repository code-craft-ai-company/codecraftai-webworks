"""
    Tests for the ConnectionManager class.
    
    This module contains unit tests and property tests for the WSGI connection
    manager functionality including keep-alive handling, connection tracking,
    and timeout management.
"""

import time
from typing import Dict

from ccai.webworks.wsgi.connectionmanager import ConnectionManager, ConnectionInfo
from ccai.webworks.wsgi.serverconfig import ServerConfig


# =============================================================================
# Unit Tests for ConnectionManager Initialization
# =============================================================================

def test_connectionmanager_default_config():
    """
        Test that ConnectionManager uses default config when none provided.
    """
    manager = ConnectionManager()
    
    # Should use default keepalive timeout of 2 seconds
    if manager.keepalive_timeout != 2:
        errmsg = f"Expected keepalive_timeout 2, got {manager.keepalive_timeout}"
        raise AssertionError(errmsg)
    
    # Should use default max_connections of 1000
    if manager.max_connections != 1000:
        errmsg = f"Expected max_connections 1000, got {manager.max_connections}"
        raise AssertionError(errmsg)
    
    return


def test_connectionmanager_custom_config():
    """
        Test that ConnectionManager uses provided config.
    """
    config = ServerConfig(keepalive=5, max_connections=500, timeout=60)
    manager = ConnectionManager(config)
    
    if manager.keepalive_timeout != 5:
        errmsg = f"Expected keepalive_timeout 5, got {manager.keepalive_timeout}"
        raise AssertionError(errmsg)
    
    if manager.max_connections != 500:
        errmsg = f"Expected max_connections 500, got {manager.max_connections}"
        raise AssertionError(errmsg)
    
    if manager.request_timeout != 60:
        errmsg = f"Expected request_timeout 60, got {manager.request_timeout}"
        raise AssertionError(errmsg)
    
    return


def test_connectionmanager_initial_connection_count():
    """
        Test that ConnectionManager starts with zero connections.
    """
    manager = ConnectionManager()
    
    if manager.active_connection_count != 0:
        errmsg = f"Expected 0 connections, got {manager.active_connection_count}"
        raise AssertionError(errmsg)
    
    return


# =============================================================================
# Unit Tests for should_keep_alive()
# =============================================================================

def test_should_keep_alive_http11_default():
    """
        Test that HTTP/1.1 defaults to keep-alive.
        
        **Property 14: Keep-Alive Connection Handling**
        **Validates: Requirements 5.9, 14.7**
    """
    manager = ConnectionManager()
    
    result = manager.should_keep_alive("HTTP/1.1", {})
    
    if result is not True:
        errmsg = "Expected HTTP/1.1 to default to keep-alive"
        raise AssertionError(errmsg)
    
    return


def test_should_keep_alive_http11_with_close():
    """
        Test that HTTP/1.1 with Connection: close returns False.
        
        **Property 14: Keep-Alive Connection Handling**
        **Validates: Requirements 5.9, 14.7**
    """
    manager = ConnectionManager()
    
    headers = {"Connection": "close"}
    result = manager.should_keep_alive("HTTP/1.1", headers)
    
    if result is not False:
        errmsg = "Expected HTTP/1.1 with Connection: close to not keep-alive"
        raise AssertionError(errmsg)
    
    return


def test_should_keep_alive_http10_default():
    """
        Test that HTTP/1.0 defaults to close.
        
        **Property 14: Keep-Alive Connection Handling**
        **Validates: Requirements 5.9, 14.7**
    """
    manager = ConnectionManager()
    
    result = manager.should_keep_alive("HTTP/1.0", {})
    
    if result is not False:
        errmsg = "Expected HTTP/1.0 to default to close"
        raise AssertionError(errmsg)
    
    return


def test_should_keep_alive_http10_with_keepalive():
    """
        Test that HTTP/1.0 with Connection: keep-alive returns True.
        
        **Property 14: Keep-Alive Connection Handling**
        **Validates: Requirements 5.9, 14.7**
    """
    manager = ConnectionManager()
    
    headers = {"Connection": "keep-alive"}
    result = manager.should_keep_alive("HTTP/1.0", headers)
    
    if result is not True:
        errmsg = "Expected HTTP/1.0 with Connection: keep-alive to keep-alive"
        raise AssertionError(errmsg)
    
    return


def test_should_keep_alive_case_insensitive_header():
    """
        Test that Connection header lookup is case-insensitive.
        
        **Property 14: Keep-Alive Connection Handling**
        **Validates: Requirements 5.9, 14.7**
    """
    manager = ConnectionManager()
    
    # Test lowercase header name
    headers = {"connection": "close"}
    result = manager.should_keep_alive("HTTP/1.1", headers)
    
    if result is not False:
        errmsg = "Expected lowercase 'connection: close' to be recognized"
        raise AssertionError(errmsg)
    
    return


def test_should_keep_alive_case_insensitive_value():
    """
        Test that Connection header value is case-insensitive.
        
        **Property 14: Keep-Alive Connection Handling**
        **Validates: Requirements 5.9, 14.7**
    """
    manager = ConnectionManager()
    
    # Test uppercase value
    headers = {"Connection": "CLOSE"}
    result = manager.should_keep_alive("HTTP/1.1", headers)
    
    if result is not False:
        errmsg = "Expected uppercase 'CLOSE' to be recognized"
        raise AssertionError(errmsg)
    
    return


def test_should_keep_alive_zero_timeout():
    """
        Test that keep-alive is disabled when timeout is 0.
        
        **Property 14: Keep-Alive Connection Handling**
        **Validates: Requirements 5.9, 14.7**
    """
    config = ServerConfig(keepalive=0)
    manager = ConnectionManager(config)
    
    # Even HTTP/1.1 should not keep-alive when timeout is 0
    result = manager.should_keep_alive("HTTP/1.1", {})
    
    if result is not False:
        errmsg = "Expected keep-alive to be disabled when timeout is 0"
        raise AssertionError(errmsg)
    
    return


def test_should_keep_alive_unknown_version():
    """
        Test that unknown HTTP version defaults to close.
        
        **Property 14: Keep-Alive Connection Handling**
        **Validates: Requirements 5.9, 14.7**
    """
    manager = ConnectionManager()
    
    result = manager.should_keep_alive("HTTP/2.0", {})
    
    if result is not False:
        errmsg = "Expected unknown HTTP version to default to close"
        raise AssertionError(errmsg)
    
    return



# =============================================================================
# Unit Tests for Connection Registration
# =============================================================================

def test_register_connection_returns_id():
    """
        Test that register_connection returns a connection ID.
    """
    manager = ConnectionManager()
    
    conn_id = manager.register_connection(("127.0.0.1", 12345))
    
    if conn_id is None:
        errmsg = "Expected connection ID, got None"
        raise AssertionError(errmsg)
    
    if not conn_id.startswith("conn-"):
        errmsg = f"Expected connection ID to start with 'conn-', got '{conn_id}'"
        raise AssertionError(errmsg)
    
    return


def test_register_connection_increments_count():
    """
        Test that registering connections increments the count.
    """
    manager = ConnectionManager()
    
    manager.register_connection(("127.0.0.1", 12345))
    
    if manager.active_connection_count != 1:
        errmsg = f"Expected 1 connection, got {manager.active_connection_count}"
        raise AssertionError(errmsg)
    
    manager.register_connection(("127.0.0.1", 12346))
    
    if manager.active_connection_count != 2:
        errmsg = f"Expected 2 connections, got {manager.active_connection_count}"
        raise AssertionError(errmsg)
    
    return


def test_register_connection_max_limit():
    """
        Test that register_connection returns None when max reached.
    """
    config = ServerConfig(max_connections=2)
    manager = ConnectionManager(config)
    
    # Register up to max
    conn1 = manager.register_connection(("127.0.0.1", 12345))
    conn2 = manager.register_connection(("127.0.0.1", 12346))
    
    if conn1 is None or conn2 is None:
        errmsg = "Expected first two connections to succeed"
        raise AssertionError(errmsg)
    
    # Third should fail
    conn3 = manager.register_connection(("127.0.0.1", 12347))
    
    if conn3 is not None:
        errmsg = "Expected third connection to fail (max reached)"
        raise AssertionError(errmsg)
    
    return


def test_unregister_connection_decrements_count():
    """
        Test that unregistering connections decrements the count.
    """
    manager = ConnectionManager()
    
    conn_id = manager.register_connection(("127.0.0.1", 12345))
    
    if manager.active_connection_count != 1:
        errmsg = f"Expected 1 connection, got {manager.active_connection_count}"
        raise AssertionError(errmsg)
    
    result = manager.unregister_connection(conn_id)
    
    if result is not True:
        errmsg = "Expected unregister to return True"
        raise AssertionError(errmsg)
    
    if manager.active_connection_count != 0:
        errmsg = f"Expected 0 connections, got {manager.active_connection_count}"
        raise AssertionError(errmsg)
    
    return


def test_unregister_nonexistent_connection():
    """
        Test that unregistering nonexistent connection returns False.
    """
    manager = ConnectionManager()
    
    result = manager.unregister_connection("nonexistent")
    
    if result is not False:
        errmsg = "Expected unregister of nonexistent to return False"
        raise AssertionError(errmsg)
    
    return


def test_get_connection_returns_info():
    """
        Test that get_connection returns connection info.
    """
    manager = ConnectionManager()
    
    conn_id = manager.register_connection(
        ("127.0.0.1", 12345),
        http_version="HTTP/1.1",
        is_keep_alive=True
    )
    
    conn_info = manager.get_connection(conn_id)
    
    if conn_info is None:
        errmsg = "Expected connection info, got None"
        raise AssertionError(errmsg)
    
    if conn_info.client_address != ("127.0.0.1", 12345):
        errmsg = f"Expected client address ('127.0.0.1', 12345), got {conn_info.client_address}"
        raise AssertionError(errmsg)
    
    if conn_info.http_version != "HTTP/1.1":
        errmsg = f"Expected HTTP version 'HTTP/1.1', got '{conn_info.http_version}'"
        raise AssertionError(errmsg)
    
    if conn_info.is_keep_alive is not True:
        errmsg = f"Expected is_keep_alive True, got {conn_info.is_keep_alive}"
        raise AssertionError(errmsg)
    
    return


def test_get_nonexistent_connection():
    """
        Test that get_connection returns None for nonexistent connection.
    """
    manager = ConnectionManager()
    
    conn_info = manager.get_connection("nonexistent")
    
    if conn_info is not None:
        errmsg = "Expected None for nonexistent connection"
        raise AssertionError(errmsg)
    
    return


def test_can_accept_connection():
    """
        Test that can_accept_connection returns correct status.
    """
    config = ServerConfig(max_connections=2)
    manager = ConnectionManager(config)
    
    # Should be able to accept initially
    if manager.can_accept_connection() is not True:
        errmsg = "Expected can_accept_connection to be True initially"
        raise AssertionError(errmsg)
    
    # Register up to max
    manager.register_connection(("127.0.0.1", 12345))
    manager.register_connection(("127.0.0.1", 12346))
    
    # Should not be able to accept more
    if manager.can_accept_connection() is not False:
        errmsg = "Expected can_accept_connection to be False at max"
        raise AssertionError(errmsg)
    
    return


# =============================================================================
# Unit Tests for Connection Activity
# =============================================================================

def test_update_connection_activity():
    """
        Test that update_connection_activity updates timestamp.
    """
    manager = ConnectionManager()
    
    conn_id = manager.register_connection(("127.0.0.1", 12345))
    conn_info = manager.get_connection(conn_id)
    
    original_activity = conn_info.last_activity
    
    # Small delay to ensure time difference
    time.sleep(0.01)
    
    result = manager.update_connection_activity(conn_id)
    
    if result is not True:
        errmsg = "Expected update_connection_activity to return True"
        raise AssertionError(errmsg)
    
    conn_info = manager.get_connection(conn_id)
    
    if conn_info.last_activity <= original_activity:
        errmsg = "Expected last_activity to be updated"
        raise AssertionError(errmsg)
    
    return


def test_increment_request_count():
    """
        Test that increment_request_count increments counter.
    """
    manager = ConnectionManager()
    
    conn_id = manager.register_connection(("127.0.0.1", 12345))
    conn_info = manager.get_connection(conn_id)
    
    if conn_info.request_count != 0:
        errmsg = f"Expected initial request_count 0, got {conn_info.request_count}"
        raise AssertionError(errmsg)
    
    manager.increment_request_count(conn_id)
    
    conn_info = manager.get_connection(conn_id)
    
    if conn_info.request_count != 1:
        errmsg = f"Expected request_count 1, got {conn_info.request_count}"
        raise AssertionError(errmsg)
    
    return


def test_set_keep_alive():
    """
        Test that set_keep_alive updates the flag.
    """
    manager = ConnectionManager()
    
    conn_id = manager.register_connection(("127.0.0.1", 12345), is_keep_alive=False)
    conn_info = manager.get_connection(conn_id)
    
    if conn_info.is_keep_alive is not False:
        errmsg = "Expected initial is_keep_alive False"
        raise AssertionError(errmsg)
    
    result = manager.set_keep_alive(conn_id, True)
    
    if result is not True:
        errmsg = "Expected set_keep_alive to return True"
        raise AssertionError(errmsg)
    
    conn_info = manager.get_connection(conn_id)
    
    if conn_info.is_keep_alive is not True:
        errmsg = "Expected is_keep_alive to be True after update"
        raise AssertionError(errmsg)
    
    return



# =============================================================================
# Unit Tests for Timeout Handling
# =============================================================================

def test_is_connection_idle_false_when_active():
    """
        Test that is_connection_idle returns False for active connection.
    """
    config = ServerConfig(keepalive=10)  # 10 second timeout
    manager = ConnectionManager(config)
    
    conn_id = manager.register_connection(("127.0.0.1", 12345), is_keep_alive=True)
    
    # Should not be idle immediately
    result = manager.is_connection_idle(conn_id)
    
    if result is not False:
        errmsg = "Expected connection to not be idle immediately"
        raise AssertionError(errmsg)
    
    return


def test_get_idle_connections_empty_when_active():
    """
        Test that get_idle_connections returns empty set when all active.
    """
    config = ServerConfig(keepalive=10)  # 10 second timeout
    manager = ConnectionManager(config)
    
    manager.register_connection(("127.0.0.1", 12345), is_keep_alive=True)
    manager.register_connection(("127.0.0.1", 12346), is_keep_alive=True)
    
    idle = manager.get_idle_connections()
    
    if len(idle) != 0:
        errmsg = f"Expected 0 idle connections, got {len(idle)}"
        raise AssertionError(errmsg)
    
    return


def test_close_idle_connections_returns_closed():
    """
        Test that close_idle_connections returns closed connection IDs.
    """
    # Use short timeout for testing
    config = ServerConfig(keepalive=1)
    manager = ConnectionManager(config)
    
    # Override the timeout to a very small value for testing
    manager._keepalive_timeout = 0.001
    
    conn_id = manager.register_connection(("127.0.0.1", 12345))
    manager.set_keep_alive(conn_id, True)
    
    # Small delay to ensure idle
    time.sleep(0.01)
    
    closed = manager.close_idle_connections()
    
    if conn_id not in closed:
        errmsg = f"Expected {conn_id} to be in closed set"
        raise AssertionError(errmsg)
    
    if manager.active_connection_count != 0:
        errmsg = f"Expected 0 connections after close, got {manager.active_connection_count}"
        raise AssertionError(errmsg)
    
    return


def test_close_timed_out_connections():
    """
        Test that close_timed_out_connections closes timed out connections.
    """
    # Use very short timeout for testing (0.001 seconds = 1ms)
    config = ServerConfig(timeout=1)  # 1 second timeout
    manager = ConnectionManager(config)
    
    # Override the timeout to a very small value for testing
    manager._request_timeout = 0.001
    
    conn_id = manager.register_connection(("127.0.0.1", 12345))
    
    # Small delay to ensure timeout
    time.sleep(0.01)
    
    closed = manager.close_timed_out_connections()
    
    if conn_id not in closed:
        errmsg = f"Expected {conn_id} to be in closed set"
        raise AssertionError(errmsg)
    
    return


def test_cleanup_returns_both_sets():
    """
        Test that cleanup returns both idle and timed out sets.
    """
    config = ServerConfig(keepalive=1, timeout=1)
    manager = ConnectionManager(config)
    
    # Override timeouts to very small values for testing
    manager._keepalive_timeout = 0.001
    manager._request_timeout = 0.001
    
    conn_id = manager.register_connection(("127.0.0.1", 12345))
    manager.set_keep_alive(conn_id, True)
    
    time.sleep(0.01)
    
    idle_closed, timed_out_closed = manager.cleanup()
    
    # Connection should be in one of the sets
    if conn_id not in idle_closed and conn_id not in timed_out_closed:
        errmsg = f"Expected {conn_id} to be in one of the closed sets"
        raise AssertionError(errmsg)
    
    return


def test_clear_all_removes_all_connections():
    """
        Test that clear_all removes all connections.
    """
    manager = ConnectionManager()
    
    manager.register_connection(("127.0.0.1", 12345))
    manager.register_connection(("127.0.0.1", 12346))
    manager.register_connection(("127.0.0.1", 12347))
    
    if manager.active_connection_count != 3:
        errmsg = f"Expected 3 connections, got {manager.active_connection_count}"
        raise AssertionError(errmsg)
    
    count = manager.clear_all()
    
    if count != 3:
        errmsg = f"Expected clear_all to return 3, got {count}"
        raise AssertionError(errmsg)
    
    if manager.active_connection_count != 0:
        errmsg = f"Expected 0 connections after clear, got {manager.active_connection_count}"
        raise AssertionError(errmsg)
    
    return


def test_get_all_connection_ids():
    """
        Test that get_all_connection_ids returns all IDs.
    """
    manager = ConnectionManager()
    
    conn1 = manager.register_connection(("127.0.0.1", 12345))
    conn2 = manager.register_connection(("127.0.0.1", 12346))
    
    all_ids = manager.get_all_connection_ids()
    
    if conn1 not in all_ids:
        errmsg = f"Expected {conn1} in all_ids"
        raise AssertionError(errmsg)
    
    if conn2 not in all_ids:
        errmsg = f"Expected {conn2} in all_ids"
        raise AssertionError(errmsg)
    
    if len(all_ids) != 2:
        errmsg = f"Expected 2 IDs, got {len(all_ids)}"
        raise AssertionError(errmsg)
    
    return


def test_get_connection_stats():
    """
        Test that get_connection_stats returns correct statistics.
    """
    config = ServerConfig(keepalive=5, max_connections=100, timeout=30)
    manager = ConnectionManager(config)
    
    conn1 = manager.register_connection(("127.0.0.1", 12345), is_keep_alive=True)
    conn2 = manager.register_connection(("127.0.0.1", 12346), is_keep_alive=False)
    
    manager.increment_request_count(conn1)
    manager.increment_request_count(conn1)
    manager.increment_request_count(conn2)
    
    stats = manager.get_connection_stats()
    
    if stats["total_connections"] != 2:
        errmsg = f"Expected total_connections 2, got {stats['total_connections']}"
        raise AssertionError(errmsg)
    
    if stats["keep_alive_connections"] != 1:
        errmsg = f"Expected keep_alive_connections 1, got {stats['keep_alive_connections']}"
        raise AssertionError(errmsg)
    
    if stats["max_connections"] != 100:
        errmsg = f"Expected max_connections 100, got {stats['max_connections']}"
        raise AssertionError(errmsg)
    
    if stats["total_requests"] != 3:
        errmsg = f"Expected total_requests 3, got {stats['total_requests']}"
        raise AssertionError(errmsg)
    
    return


# =============================================================================
# Unit Tests for ConnectionInfo
# =============================================================================

def test_connectioninfo_idle_time():
    """
        Test that ConnectionInfo.idle_time returns correct value.
    """
    conn_info = ConnectionInfo(
        connection_id="test-1",
        client_address=("127.0.0.1", 12345)
    )
    
    # Small delay
    time.sleep(0.05)
    
    idle_time = conn_info.idle_time()
    
    if idle_time < 0.04:
        errmsg = f"Expected idle_time >= 0.04, got {idle_time}"
        raise AssertionError(errmsg)
    
    return


def test_connectioninfo_age():
    """
        Test that ConnectionInfo.age returns correct value.
    """
    conn_info = ConnectionInfo(
        connection_id="test-1",
        client_address=("127.0.0.1", 12345)
    )
    
    # Small delay
    time.sleep(0.05)
    
    age = conn_info.age()
    
    if age < 0.04:
        errmsg = f"Expected age >= 0.04, got {age}"
        raise AssertionError(errmsg)
    
    return


def test_connectioninfo_update_activity():
    """
        Test that ConnectionInfo.update_activity updates timestamp.
    """
    conn_info = ConnectionInfo(
        connection_id="test-1",
        client_address=("127.0.0.1", 12345)
    )
    
    original = conn_info.last_activity
    
    time.sleep(0.01)
    
    conn_info.update_activity()
    
    if conn_info.last_activity <= original:
        errmsg = "Expected last_activity to be updated"
        raise AssertionError(errmsg)
    
    return


def test_connectioninfo_increment_request_count():
    """
        Test that ConnectionInfo.increment_request_count increments counter.
    """
    conn_info = ConnectionInfo(
        connection_id="test-1",
        client_address=("127.0.0.1", 12345)
    )
    
    if conn_info.request_count != 0:
        errmsg = f"Expected initial request_count 0, got {conn_info.request_count}"
        raise AssertionError(errmsg)
    
    conn_info.increment_request_count()
    
    if conn_info.request_count != 1:
        errmsg = f"Expected request_count 1, got {conn_info.request_count}"
        raise AssertionError(errmsg)
    
    conn_info.increment_request_count()
    
    if conn_info.request_count != 2:
        errmsg = f"Expected request_count 2, got {conn_info.request_count}"
        raise AssertionError(errmsg)
    
    return


# =============================================================================
# Property Test for Keep-Alive Handling
# =============================================================================

def test_property_keep_alive_http11_without_close_header():
    """
        Property 14: Keep-Alive Connection Handling
        
        For any HTTP/1.1 request without Connection: close header,
        the server SHALL keep the connection open.
        
        **Validates: Requirements 5.9, 14.7**
    """
    manager = ConnectionManager()
    
    # Test various header combinations for HTTP/1.1
    test_cases = [
        {},  # No headers
        {"Content-Type": "text/html"},  # Unrelated header
        {"Connection": "keep-alive"},  # Explicit keep-alive
        {"Connection": "Keep-Alive"},  # Case variation
        {"Host": "example.com"},  # Host header only
        {"Accept": "text/html", "Accept-Language": "en"},  # Multiple headers
    ]
    
    for headers in test_cases:
        result = manager.should_keep_alive("HTTP/1.1", headers)
        
        if result is not True:
            errmsg = f"HTTP/1.1 with headers {headers} should keep-alive"
            raise AssertionError(errmsg)
    
    return


def test_property_keep_alive_http11_with_close_header():
    """
        Property 14: Keep-Alive Connection Handling
        
        For any HTTP/1.1 request with Connection: close header,
        the server SHALL close the connection.
        
        **Validates: Requirements 5.9, 14.7**
    """
    manager = ConnectionManager()
    
    # Test various ways to specify close
    test_cases = [
        {"Connection": "close"},
        {"Connection": "Close"},
        {"Connection": "CLOSE"},
        {"connection": "close"},  # Lowercase header name
        {"Connection": " close "},  # With whitespace
    ]
    
    for headers in test_cases:
        result = manager.should_keep_alive("HTTP/1.1", headers)
        
        if result is not False:
            errmsg = f"HTTP/1.1 with headers {headers} should close"
            raise AssertionError(errmsg)
    
    return


def test_property_keep_alive_http10_default_close():
    """
        Property 14: Keep-Alive Connection Handling
        
        For any HTTP/1.0 request without Connection: keep-alive header,
        the server SHALL close the connection.
        
        **Validates: Requirements 5.9, 14.7**
    """
    manager = ConnectionManager()
    
    # Test various header combinations for HTTP/1.0
    test_cases = [
        {},  # No headers
        {"Content-Type": "text/html"},  # Unrelated header
        {"Connection": "close"},  # Explicit close
        {"Host": "example.com"},  # Host header only
    ]
    
    for headers in test_cases:
        result = manager.should_keep_alive("HTTP/1.0", headers)
        
        if result is not False:
            errmsg = f"HTTP/1.0 with headers {headers} should close"
            raise AssertionError(errmsg)
    
    return


def test_property_keep_alive_http10_with_keepalive_header():
    """
        Property 14: Keep-Alive Connection Handling
        
        For any HTTP/1.0 request with Connection: keep-alive header,
        the server SHALL keep the connection open.
        
        **Validates: Requirements 5.9, 14.7**
    """
    manager = ConnectionManager()
    
    # Test various ways to specify keep-alive
    test_cases = [
        {"Connection": "keep-alive"},
        {"Connection": "Keep-Alive"},
        {"Connection": "KEEP-ALIVE"},
        {"connection": "keep-alive"},  # Lowercase header name
    ]
    
    for headers in test_cases:
        result = manager.should_keep_alive("HTTP/1.0", headers)
        
        if result is not True:
            errmsg = f"HTTP/1.0 with headers {headers} should keep-alive"
            raise AssertionError(errmsg)
    
    return


def test_property_keep_alive_timeout_expiry():
    """
        Property 14: Keep-Alive Connection Handling
        
        For any keep-alive connection, the server SHALL close it
        when the keep-alive timeout expires.
        
        **Validates: Requirements 5.9, 14.7**
    """
    # Use short timeout for testing
    config = ServerConfig(keepalive=1)
    manager = ConnectionManager(config)
    
    # Override the timeout to a very small value for testing
    manager._keepalive_timeout = 0.001
    
    # Register a keep-alive connection
    conn_id = manager.register_connection(("127.0.0.1", 12345))
    manager.set_keep_alive(conn_id, True)
    
    # Small delay to ensure timeout
    time.sleep(0.01)
    
    # Connection should be idle
    idle_connections = manager.get_idle_connections()
    
    if conn_id not in idle_connections:
        errmsg = f"Expected {conn_id} to be idle after timeout"
        raise AssertionError(errmsg)
    
    # Close idle connections
    closed = manager.close_idle_connections()
    
    if conn_id not in closed:
        errmsg = f"Expected {conn_id} to be closed"
        raise AssertionError(errmsg)
    
    # Connection should no longer exist
    conn_info = manager.get_connection(conn_id)
    
    if conn_info is not None:
        errmsg = "Expected connection to be removed after close"
        raise AssertionError(errmsg)
    
    return

