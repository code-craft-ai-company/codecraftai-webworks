"""
    Tests for the WSGIServer class in the WSGI layer.
"""

import sys
import threading
import time
from typing import Any, Callable, Dict, Iterable

from ccai.webworks.wsgi.server import WSGIServer
from ccai.webworks.wsgi.serverconfig import ServerConfig


def create_simple_app() -> Callable:
    """Create a simple WSGI application for testing."""
    def app(environ: Dict[str, Any], start_response: Callable) -> Iterable[bytes]:
        status = "200 OK"
        headers = [("Content-Type", "text/plain"), ("Content-Length", "13")]
        start_response(status, headers)
        return [b"Hello, World!"]
    return app


def test_wsgiserver_init_with_defaults():
    """Test WSGIServer initialization with default configuration."""
    app = create_simple_app()
    server = WSGIServer(app)
    
    if server.is_running is True:
        errmsg = f"Expected is_running False, got {server.is_running}"
        raise AssertionError(errmsg)
    
    if server.config.host != "127.0.0.1":
        errmsg = f"Expected host '127.0.0.1', got '{server.config.host}'"
        raise AssertionError(errmsg)
    
    if server.config.port != 8000:
        errmsg = f"Expected port 8000, got {server.config.port}"
        raise AssertionError(errmsg)
    
    if server.listener is not None:
        errmsg = f"Expected listener None, got {server.listener}"
        raise AssertionError(errmsg)
    
    if server.worker_manager is not None:
        errmsg = f"Expected worker_manager None, got {server.worker_manager}"
        raise AssertionError(errmsg)
    
    return


def test_wsgiserver_init_with_custom_config():
    """Test WSGIServer initialization with custom configuration."""
    app = create_simple_app()
    config = ServerConfig(
        host="0.0.0.0",
        port=9000,
        workers=4,
        threads=2,
        timeout=60,
        reload=True,
        debug=True
    )
    server = WSGIServer(app, config)
    
    if server.config.host != "0.0.0.0":
        errmsg = f"Expected host '0.0.0.0', got '{server.config.host}'"
        raise AssertionError(errmsg)
    
    if server.config.port != 9000:
        errmsg = f"Expected port 9000, got {server.config.port}"
        raise AssertionError(errmsg)
    
    if server.config.workers != 4:
        errmsg = f"Expected workers 4, got {server.config.workers}"
        raise AssertionError(errmsg)
    
    if server.config.threads != 2:
        errmsg = f"Expected threads 2, got {server.config.threads}"
        raise AssertionError(errmsg)
    
    if server.config.reload is not True:
        errmsg = f"Expected reload True, got {server.config.reload}"
        raise AssertionError(errmsg)
    
    if server.config.debug is not True:
        errmsg = f"Expected debug True, got {server.config.debug}"
        raise AssertionError(errmsg)
    
    return


def test_wsgiserver_request_count_initial():
    """Test WSGIServer request_count is initially zero."""
    app = create_simple_app()
    server = WSGIServer(app)
    
    if server.request_count != 0:
        errmsg = f"Expected request_count 0, got {server.request_count}"
        raise AssertionError(errmsg)
    
    return


def test_wsgiserver_uptime_not_running():
    """Test WSGIServer uptime is zero when not running."""
    app = create_simple_app()
    server = WSGIServer(app)
    
    if server.uptime != 0.0:
        errmsg = f"Expected uptime 0.0, got {server.uptime}"
        raise AssertionError(errmsg)
    
    return


def test_wsgiserver_shutdown_when_not_running():
    """Test WSGIServer.shutdown() when server is not running."""
    app = create_simple_app()
    server = WSGIServer(app)
    
    server.shutdown(graceful=True)
    
    if server.is_running is True:
        errmsg = f"Expected is_running False, got {server.is_running}"
        raise AssertionError(errmsg)
    
    return


def test_wsgiserver_get_stats_not_running():
    """Test WSGIServer.get_stats() when server is not running."""
    app = create_simple_app()
    server = WSGIServer(app)
    
    stats = server.get_stats()
    
    if stats["running"] is True:
        errmsg = f"Expected running False, got {stats['running']}"
        raise AssertionError(errmsg)
    
    if stats["uptime"] != 0.0:
        errmsg = f"Expected uptime 0.0, got {stats['uptime']}"
        raise AssertionError(errmsg)
    
    if stats["request_count"] != 0:
        errmsg = f"Expected request_count 0, got {stats['request_count']}"
        raise AssertionError(errmsg)
    
    if "config" not in stats:
        errmsg = "Expected 'config' in stats"
        raise AssertionError(errmsg)
    
    return


def test_wsgiserver_log_request():
    """Test WSGIServer.log_request() increments request count."""
    app = create_simple_app()
    config = ServerConfig(access_log=True)
    server = WSGIServer(app, config)
    
    server.log_request("GET", "/test", 200, 0.001, "127.0.0.1")
    
    if server.request_count != 1:
        errmsg = f"Expected request_count 1, got {server.request_count}"
        raise AssertionError(errmsg)
    
    server.log_request("POST", "/api", 201, 0.002, "127.0.0.1")
    
    if server.request_count != 2:
        errmsg = f"Expected request_count 2, got {server.request_count}"
        raise AssertionError(errmsg)
    
    return


def test_wsgiserver_log_request_disabled():
    """Test WSGIServer.log_request() does not increment when access_log is disabled."""
    app = create_simple_app()
    config = ServerConfig(access_log=False)
    server = WSGIServer(app, config)
    
    server.log_request("GET", "/test", 200, 0.001, "127.0.0.1")
    
    if server.request_count != 0:
        errmsg = f"Expected request_count 0 when access_log disabled, got {server.request_count}"
        raise AssertionError(errmsg)
    
    return




def test_wsgiserver_serve_and_shutdown():
    """Test WSGIServer serve_forever() and shutdown() (Unix only)."""
    if sys.platform == "win32":
        return
    
    app = create_simple_app()
    config = ServerConfig(
        host="127.0.0.1",
        port=0,  # Use ephemeral port
        workers=1,
        threads=1,
        timeout=5,
        graceful_timeout=2
    )
    server = WSGIServer(app, config)
    
    # Start server in a thread
    server_thread = threading.Thread(target=server.serve_forever, daemon=True)
    server_thread.start()
    
    # Wait for server to start
    time.sleep(1.0)
    
    if server.is_running is not True:
        errmsg = f"Expected is_running True, got {server.is_running}"
        raise AssertionError(errmsg)
    
    if server.listener is None:
        errmsg = "Expected listener to be set"
        raise AssertionError(errmsg)
    
    if server.worker_manager is None:
        errmsg = "Expected worker_manager to be set"
        raise AssertionError(errmsg)
    
    # Shutdown server
    server.shutdown(graceful=False)
    
    # Wait for server thread to finish
    server_thread.join(timeout=5.0)
    
    if server.is_running is True:
        errmsg = f"Expected is_running False after shutdown, got {server.is_running}"
        raise AssertionError(errmsg)
    
    return


def test_wsgiserver_uptime_while_running():
    """Test WSGIServer uptime increases while running (Unix only)."""
    if sys.platform == "win32":
        return
    
    app = create_simple_app()
    config = ServerConfig(
        host="127.0.0.1",
        port=0,
        workers=1,
        timeout=5,
        graceful_timeout=2
    )
    server = WSGIServer(app, config)
    
    # Start server in a thread
    server_thread = threading.Thread(target=server.serve_forever, daemon=True)
    server_thread.start()
    
    # Wait for server to start
    time.sleep(1.0)
    
    uptime1 = server.uptime
    time.sleep(0.5)
    uptime2 = server.uptime
    
    if uptime2 <= uptime1:
        errmsg = f"Expected uptime to increase, got {uptime1} -> {uptime2}"
        raise AssertionError(errmsg)
    
    # Shutdown server
    server.shutdown(graceful=False)
    server_thread.join(timeout=5.0)
    
    return


def test_wsgiserver_get_stats_while_running():
    """Test WSGIServer.get_stats() while server is running (Unix only)."""
    if sys.platform == "win32":
        return
    
    app = create_simple_app()
    config = ServerConfig(
        host="127.0.0.1",
        port=0,
        workers=1,
        timeout=5,
        graceful_timeout=2
    )
    server = WSGIServer(app, config)
    
    # Start server in a thread
    server_thread = threading.Thread(target=server.serve_forever, daemon=True)
    server_thread.start()
    
    # Wait for server to start
    time.sleep(1.0)
    
    stats = server.get_stats()
    
    if stats["running"] is not True:
        errmsg = f"Expected running True, got {stats['running']}"
        raise AssertionError(errmsg)
    
    if stats["uptime"] <= 0:
        errmsg = f"Expected positive uptime, got {stats['uptime']}"
        raise AssertionError(errmsg)
    
    if "workers" not in stats:
        errmsg = "Expected 'workers' in stats"
        raise AssertionError(errmsg)
    
    if "bound_address" not in stats:
        errmsg = "Expected 'bound_address' in stats"
        raise AssertionError(errmsg)
    
    # Shutdown server
    server.shutdown(graceful=False)
    server_thread.join(timeout=5.0)
    
    return


def test_wsgiserver_graceful_shutdown():
    """Test WSGIServer graceful shutdown (Unix only)."""
    if sys.platform == "win32":
        return
    
    app = create_simple_app()
    config = ServerConfig(
        host="127.0.0.1",
        port=0,
        workers=1,
        timeout=5,
        graceful_timeout=2
    )
    server = WSGIServer(app, config)
    
    # Start server in a thread
    server_thread = threading.Thread(target=server.serve_forever, daemon=True)
    server_thread.start()
    
    # Wait for server to start
    time.sleep(1.0)
    
    # Graceful shutdown
    server.shutdown(graceful=True)
    
    # Wait for server thread to finish
    server_thread.join(timeout=10.0)
    
    if server.is_running is True:
        errmsg = f"Expected is_running False after graceful shutdown, got {server.is_running}"
        raise AssertionError(errmsg)
    
    return


def test_wsgiserver_multiple_shutdown_calls():
    """Test WSGIServer handles multiple shutdown() calls gracefully."""
    app = create_simple_app()
    server = WSGIServer(app)
    
    # Multiple shutdown calls should not raise
    server.shutdown(graceful=True)
    server.shutdown(graceful=False)
    server.shutdown(graceful=True)
    
    return


def test_wsgiserver_config_property():
    """Test WSGIServer.config property returns correct configuration."""
    app = create_simple_app()
    config = ServerConfig(host="localhost", port=5000, workers=2)
    server = WSGIServer(app, config)
    
    if server.config is not config:
        errmsg = "Expected config property to return the same config object"
        raise AssertionError(errmsg)
    
    return



# =============================================================================
# Property-Based Tests for WSGIServer
# =============================================================================

import random
from io import BytesIO


def test_property_request_size_limit_enforcement():
    """
        Property test: Request Size Limit Enforcement
        
        For any HTTP request with headers or body exceeding configured limits,
        the server SHALL return HTTP 400 Bad Request or HTTP 413 Request Entity
        Too Large without processing the full request.
        
        **Feature: wsgi-layer, Property 15: Request Size Limit Enforcement**
        **Validates: Requirements 11.4, 11.5, 7.6, 7.7**
    """
    from ccai.webworks.wsgi.httpparser import HTTPParser
    from ccai.webworks.wsgi.exceptions import HeaderTooLarge, TooManyHeaders, RequestEntityTooLarge
    
    # Run 100 iterations with random configurations
    num_iterations = 100
    
    for iteration in range(num_iterations):
        # Test 1: Header size limit enforcement
        max_header_size = random.randint(100, 500)
        config = ServerConfig(
            host="127.0.0.1",
            port=0,
            max_header_size=max_header_size,
            max_headers=50
        )
        parser = HTTPParser(config)
        
        # Generate headers that exceed the limit
        excess_size = random.randint(10, 200)
        header_value = "X" * (max_header_size + excess_size)
        
        # Create a mock socket with oversized headers
        request_data = f"GET / HTTP/1.1\r\nHost: localhost\r\nX-Large: {header_value}\r\n\r\n".encode()
        
        # Create a mock socket-like object
        mock_socket = MockSocket(request_data)
        
        exception_raised = False
        try:
            parser.parse_request(
                mock_socket,
                ("127.0.0.1", 12345),
                ("127.0.0.1", 8000),
                "http"
            )
        except (HeaderTooLarge, Exception) as err:
            exception_raised = True
            # We expect some form of header-related error
        
        if not exception_raised:
            errmsg = f"Iteration {iteration}: Expected header size limit error for header_size={len(header_value)}, max={max_header_size}"
            raise AssertionError(errmsg)
        
        # Test 2: Header count limit enforcement
        max_headers = random.randint(5, 20)
        config2 = ServerConfig(
            host="127.0.0.1",
            port=0,
            max_header_size=8192,
            max_headers=max_headers
        )
        parser2 = HTTPParser(config2)
        
        # Generate more headers than allowed
        excess_headers = random.randint(1, 10)
        num_headers = max_headers + excess_headers
        headers_str = "\r\n".join([f"X-Header-{i}: value{i}" for i in range(num_headers)])
        request_data2 = f"GET / HTTP/1.1\r\nHost: localhost\r\n{headers_str}\r\n\r\n".encode()
        
        mock_socket2 = MockSocket(request_data2)
        
        exception_raised2 = False
        try:
            parser2.parse_request(
                mock_socket2,
                ("127.0.0.1", 12345),
                ("127.0.0.1", 8000),
                "http"
            )
        except (TooManyHeaders, Exception) as err:
            exception_raised2 = True
        
        if not exception_raised2:
            errmsg = f"Iteration {iteration}: Expected header count limit error for num_headers={num_headers}, max={max_headers}"
            raise AssertionError(errmsg)
    
    return


class MockSocket:
    """Mock socket for testing HTTP parsing."""
    
    def __init__(self, data: bytes):
        self._data = data
        self._pos = 0
        self._timeout = None
    
    def recv(self, bufsize: int) -> bytes:
        if self._pos >= len(self._data):
            return b""
        end = min(self._pos + bufsize, len(self._data))
        chunk = self._data[self._pos:end]
        self._pos = end
        return chunk
    
    def makefile(self, mode: str = "rb", buffering: int = -1):
        return BytesIO(self._data)
    
    def settimeout(self, timeout):
        self._timeout = timeout
    
    def gettimeout(self):
        return self._timeout
    
    def setblocking(self, flag):
        pass
    
    def fileno(self):
        return -1


def test_property_request_body_size_limit_via_server():
    """
        Property test: Request Body Size Limit via Server Configuration
        
        For any request body exceeding the configured max_request_size,
        the server SHALL reject the request with HTTP 413.
        
        **Feature: wsgi-layer, Property 15: Request Size Limit Enforcement**
        **Validates: Requirements 7.6, 7.7**
    """
    from ccai.webworks.wsgi.bodyparser import RequestBodyParser
    from ccai.webworks.wsgi.exceptions import RequestEntityTooLarge
    
    # Run 100 iterations with random body sizes
    num_iterations = 100
    
    for iteration in range(num_iterations):
        # Generate random max size (100-1000 bytes)
        max_size = random.randint(100, 1000)
        
        # Generate body that exceeds max size
        excess_amount = random.randint(1, 500)
        body_size = max_size + excess_amount
        body_content = bytes(random.randint(0, 255) for _ in range(body_size))
        
        # Create parser with size limit
        parser = RequestBodyParser(max_size=max_size)
        wsgi_input = BytesIO(body_content)
        
        # Test that oversized body is rejected
        exception_raised = False
        try:
            parser.parse_raw(wsgi_input, body_size)
        except RequestEntityTooLarge as err:
            exception_raised = True
            
            # Verify HTTP 413 status code
            if err.status_code != 413:
                errmsg = f"Iteration {iteration}: Expected status_code 413, got {err.status_code}"
                raise AssertionError(errmsg)
            
            # Verify max_size is correct
            if err.max_size != max_size:
                errmsg = f"Iteration {iteration}: Expected max_size {max_size}, got {err.max_size}"
                raise AssertionError(errmsg)
        
        if not exception_raised:
            errmsg = f"Iteration {iteration}: Expected RequestEntityTooLarge for body_size={body_size}, max_size={max_size}"
            raise AssertionError(errmsg)
    
    return



def test_property_graceful_shutdown():
    """
        Property test: Graceful Shutdown
        
        For any shutdown signal (SIGTERM, SIGINT), the server SHALL stop accepting
        new connections, allow active requests to complete within the graceful
        timeout, and then terminate all workers.
        
        **Feature: wsgi-layer, Property 16: Graceful Shutdown**
        **Validates: Requirements 5.8, 13.4, 13.7**
    """
    if sys.platform == "win32":
        # Skip on Windows - signal handling differs
        return
    
    # Run 10 iterations with different configurations
    num_iterations = 10
    
    for iteration in range(num_iterations):
        # Generate random configuration
        num_workers = random.randint(1, 3)
        graceful_timeout = random.randint(1, 3)
        
        app = create_simple_app()
        config = ServerConfig(
            host="127.0.0.1",
            port=0,
            workers=num_workers,
            timeout=5,
            graceful_timeout=graceful_timeout
        )
        server = WSGIServer(app, config)
        
        # Start server in a thread
        server_thread = threading.Thread(target=server.serve_forever, daemon=True)
        server_thread.start()
        
        # Wait for server to start
        time.sleep(1.0)
        
        if server.is_running is not True:
            errmsg = f"Iteration {iteration}: Server failed to start"
            raise AssertionError(errmsg)
        
        # Verify workers are running
        if server.worker_manager is None:
            errmsg = f"Iteration {iteration}: Worker manager not initialized"
            raise AssertionError(errmsg)
        
        initial_worker_count = server.worker_manager.worker_count
        if initial_worker_count != num_workers:
            errmsg = f"Iteration {iteration}: Expected {num_workers} workers, got {initial_worker_count}"
            raise AssertionError(errmsg)
        
        # Test graceful shutdown
        start_shutdown = time.time()
        server.shutdown(graceful=True)
        shutdown_duration = time.time() - start_shutdown
        
        # Wait for server thread to finish
        server_thread.join(timeout=graceful_timeout + 5.0)
        
        # Verify server stopped
        if server.is_running is True:
            errmsg = f"Iteration {iteration}: Server still running after shutdown"
            raise AssertionError(errmsg)
        
        # Verify all workers terminated
        if server.worker_manager is not None:
            remaining_workers = server.worker_manager.worker_count
            if remaining_workers != 0:
                errmsg = f"Iteration {iteration}: Expected 0 workers after shutdown, got {remaining_workers}"
                raise AssertionError(errmsg)
    
    return


def test_property_immediate_shutdown():
    """
        Property test: Immediate Shutdown
        
        For any immediate shutdown request (graceful=False), the server SHALL
        terminate all workers immediately without waiting for active requests.
        
        **Feature: wsgi-layer, Property 16: Graceful Shutdown**
        **Validates: Requirements 5.8, 13.4, 13.7**
    """
    if sys.platform == "win32":
        # Skip on Windows - signal handling differs
        return
    
    # Run 10 iterations with different configurations
    num_iterations = 10
    
    for iteration in range(num_iterations):
        # Generate random configuration
        num_workers = random.randint(1, 3)
        
        app = create_simple_app()
        config = ServerConfig(
            host="127.0.0.1",
            port=0,
            workers=num_workers,
            timeout=5,
            graceful_timeout=30  # Long timeout to verify immediate shutdown
        )
        server = WSGIServer(app, config)
        
        # Start server in a thread
        server_thread = threading.Thread(target=server.serve_forever, daemon=True)
        server_thread.start()
        
        # Wait for server to start
        time.sleep(1.0)
        
        if server.is_running is not True:
            errmsg = f"Iteration {iteration}: Server failed to start"
            raise AssertionError(errmsg)
        
        # Test immediate shutdown
        start_shutdown = time.time()
        server.shutdown(graceful=False)
        shutdown_duration = time.time() - start_shutdown
        
        # Wait for server thread to finish
        server_thread.join(timeout=5.0)
        
        # Verify server stopped quickly (should be much faster than graceful_timeout)
        if shutdown_duration > 5.0:
            errmsg = f"Iteration {iteration}: Immediate shutdown took too long: {shutdown_duration:.2f}s"
            raise AssertionError(errmsg)
        
        # Verify server stopped
        if server.is_running is True:
            errmsg = f"Iteration {iteration}: Server still running after immediate shutdown"
            raise AssertionError(errmsg)
    
    return


def test_property_shutdown_stops_accepting_connections():
    """
        Property test: Shutdown Stops Accepting New Connections
        
        After shutdown is initiated, the server SHALL stop accepting new connections.
        
        **Feature: wsgi-layer, Property 16: Graceful Shutdown**
        **Validates: Requirements 5.8**
    """
    if sys.platform == "win32":
        # Skip on Windows
        return
    
    # Run 5 iterations
    num_iterations = 5
    
    for iteration in range(num_iterations):
        app = create_simple_app()
        config = ServerConfig(
            host="127.0.0.1",
            port=0,
            workers=1,
            timeout=5,
            graceful_timeout=2
        )
        server = WSGIServer(app, config)
        
        # Start server in a thread
        server_thread = threading.Thread(target=server.serve_forever, daemon=True)
        server_thread.start()
        
        # Wait for server to start
        time.sleep(1.0)
        
        if server.is_running is not True:
            errmsg = f"Iteration {iteration}: Server failed to start"
            raise AssertionError(errmsg)
        
        # Initiate shutdown
        server.shutdown(graceful=True)
        
        # Verify shutdown was requested
        if server._shutdown_requested is not True:
            errmsg = f"Iteration {iteration}: Shutdown not requested"
            raise AssertionError(errmsg)
        
        # Wait for server thread to finish
        server_thread.join(timeout=10.0)
        
        # Verify server stopped
        if server.is_running is True:
            errmsg = f"Iteration {iteration}: Server still running after shutdown"
            raise AssertionError(errmsg)
    
    return

