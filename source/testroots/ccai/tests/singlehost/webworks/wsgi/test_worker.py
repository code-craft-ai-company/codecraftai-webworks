"""
    Tests for the Worker class in the WSGI layer.
    
    This module contains tests for the Worker class which handles HTTP requests
    in the built-in WSGI server.
"""

import io
import socket
import threading
import time
from typing import Any, Callable, Dict, Iterable, List, Tuple

from ccai.webworks.wsgi.worker import Worker
from ccai.webworks.wsgi.serverconfig import ServerConfig
from ccai.webworks.wsgi.socketlistener import SocketListener


# ============================================================================
# Test Fixtures
# ============================================================================

def create_simple_app() -> Callable:
    """
        Create a simple WSGI application for testing.
        
        :returns: WSGI application callable.
    """
    def app(environ: Dict[str, Any], start_response: Callable) -> Iterable[bytes]:
        status = "200 OK"
        headers = [
            ("Content-Type", "text/plain"),
            ("Content-Length", "13"),
        ]
        start_response(status, headers)
        return [b"Hello, World!"]
    
    return app


def create_echo_app() -> Callable:
    """
        Create a WSGI application that echoes the request body.
        
        :returns: WSGI application callable.
    """
    def app(environ: Dict[str, Any], start_response: Callable) -> Iterable[bytes]:
        # Read request body
        content_length = environ.get("CONTENT_LENGTH", "0")
        try:
            length = int(content_length)
        except ValueError:
            length = 0
        
        body = environ["wsgi.input"].read(length)
        
        status = "200 OK"
        headers = [
            ("Content-Type", "text/plain"),
            ("Content-Length", str(len(body))),
        ]
        start_response(status, headers)
        return [body]
    
    return app


def create_error_app() -> Callable:
    """
        Create a WSGI application that raises an exception.
        
        :returns: WSGI application callable.
    """
    def app(environ: Dict[str, Any], start_response: Callable) -> Iterable[bytes]:
        raise ValueError("Test error")
    
    return app


def create_status_app(status_code: int, message: str) -> Callable:
    """
        Create a WSGI application that returns a specific status.
        
        :param status_code: HTTP status code.
        :param message: Status message.
        
        :returns: WSGI application callable.
    """
    def app(environ: Dict[str, Any], start_response: Callable) -> Iterable[bytes]:
        status = f"{status_code} {message}"
        body = message.encode("utf-8")
        headers = [
            ("Content-Type", "text/plain"),
            ("Content-Length", str(len(body))),
        ]
        start_response(status, headers)
        return [body]
    
    return app


def create_mock_listener(host: str = "127.0.0.1", port: int = 0) -> SocketListener:
    """
        Create a mock socket listener for testing.
        
        :param host: Host to bind to.
        :param port: Port to bind to (0 for ephemeral).
        
        :returns: SocketListener instance.
    """
    config = ServerConfig(host=host, port=port)
    listener = SocketListener(config)
    listener.bind()
    return listener


def send_http_request(
    host: str,
    port: int,
    method: str = "GET",
    path: str = "/",
    headers: Dict[str, str] = None,
    body: bytes = b""
) -> Tuple[int, Dict[str, str], bytes]:
    """
        Send an HTTP request and return the response.
        
        :param host: Server host.
        :param port: Server port.
        :param method: HTTP method.
        :param path: Request path.
        :param headers: Request headers.
        :param body: Request body.
        
        :returns: Tuple of (status_code, headers, body).
    """
    if headers is None:
        headers = {}
    
    # Build request
    request_lines = [f"{method} {path} HTTP/1.1"]
    request_lines.append(f"Host: {host}:{port}")
    
    if len(body) > 0:
        headers["Content-Length"] = str(len(body))
    
    for name, value in headers.items():
        request_lines.append(f"{name}: {value}")
    
    request_lines.append("")  # Empty line to end headers
    
    # Join with CRLF and encode
    request = "\r\n".join(request_lines).encode("utf-8")
    request += b"\r\n"  # Add final CRLF after headers
    
    # Append body if present
    if len(body) > 0:
        request += body
    
    # Connect and send
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(5.0)
    
    try:
        sock.connect((host, port))
        sock.sendall(request)
        
        # Receive response
        response = b""
        while True:
            try:
                chunk = sock.recv(4096)
                if len(chunk) == 0:
                    break
                response += chunk
                
                # Check if we have complete response
                if b"\r\n\r\n" in response:
                    header_end = response.index(b"\r\n\r\n")
                    header_part = response[:header_end].decode("utf-8")
                    
                    # Check for Content-Length
                    content_length = 0
                    for line in header_part.split("\r\n"):
                        if line.lower().startswith("content-length:"):
                            content_length = int(line.split(":", 1)[1].strip())
                            break
                    
                    body_start = header_end + 4
                    if len(response) >= body_start + content_length:
                        break
            except socket.timeout:
                break
    finally:
        sock.close()
    
    # Parse response
    if b"\r\n\r\n" not in response:
        return (0, {}, b"")
    
    header_end = response.index(b"\r\n\r\n")
    header_part = response[:header_end].decode("utf-8")
    body_part = response[header_end + 4:]
    
    # Parse status line
    lines = header_part.split("\r\n")
    status_line = lines[0]
    parts = status_line.split(" ", 2)
    status_code = int(parts[1])
    
    # Parse headers
    response_headers: Dict[str, str] = {}
    for line in lines[1:]:
        if ":" in line:
            name, value = line.split(":", 1)
            response_headers[name.strip()] = value.strip()
    
    return (status_code, response_headers, body_part)


# ============================================================================
# Tests for Worker Initialization
# ============================================================================

def test_worker_init_with_defaults():
    """
        Test Worker initialization with default configuration.
    """
    app = create_simple_app()
    config = ServerConfig()
    listener = create_mock_listener()
    
    try:
        worker = Worker(app, listener, config, worker_id=1)
        
        if worker.worker_id != 1:
            errmsg = f"Expected worker_id 1, got {worker.worker_id}"
            raise AssertionError(errmsg)
        
        if worker.is_running != False:
            errmsg = f"Expected is_running False, got {worker.is_running}"
            raise AssertionError(errmsg)
        
        if worker.active_connections != 0:
            errmsg = f"Expected active_connections 0, got {worker.active_connections}"
            raise AssertionError(errmsg)
        
        if worker.total_requests != 0:
            errmsg = f"Expected total_requests 0, got {worker.total_requests}"
            raise AssertionError(errmsg)
        
        if worker.config is not config:
            errmsg = "Expected config to be the same instance"
            raise AssertionError(errmsg)
    finally:
        listener.close()
    
    return


def test_worker_init_with_custom_config():
    """
        Test Worker initialization with custom configuration.
    """
    app = create_simple_app()
    config = ServerConfig(
        host="127.0.0.1",
        port=0,
        workers=2,
        threads=4,
        timeout=60,
        keepalive=5
    )
    listener = create_mock_listener()
    
    try:
        worker = Worker(app, listener, config, worker_id=42)
        
        if worker.worker_id != 42:
            errmsg = f"Expected worker_id 42, got {worker.worker_id}"
            raise AssertionError(errmsg)
        
        if worker.config.threads != 4:
            errmsg = f"Expected threads 4, got {worker.config.threads}"
            raise AssertionError(errmsg)
        
        if worker.config.timeout != 60:
            errmsg = f"Expected timeout 60, got {worker.config.timeout}"
            raise AssertionError(errmsg)
        
        if worker.config.keepalive != 5:
            errmsg = f"Expected keepalive 5, got {worker.config.keepalive}"
            raise AssertionError(errmsg)
    finally:
        listener.close()
    
    return


def test_worker_init_without_config():
    """
        Test Worker initialization without explicit configuration.
    """
    app = create_simple_app()
    listener = create_mock_listener()
    
    try:
        worker = Worker(app, listener)
        
        if worker.worker_id != 0:
            errmsg = f"Expected worker_id 0, got {worker.worker_id}"
            raise AssertionError(errmsg)
        
        if worker.is_running != False:
            errmsg = f"Expected is_running False, got {worker.is_running}"
            raise AssertionError(errmsg)
        
        # Should use default config
        if worker.config.host != "127.0.0.1":
            errmsg = f"Expected host '127.0.0.1', got '{worker.config.host}'"
            raise AssertionError(errmsg)
        
        if worker.config.port != 8000:
            errmsg = f"Expected port 8000, got {worker.config.port}"
            raise AssertionError(errmsg)
    finally:
        listener.close()
    
    return


# ============================================================================
# Tests for Worker Statistics
# ============================================================================

def test_worker_get_stats():
    """
        Test Worker.get_stats() returns correct statistics.
    """
    app = create_simple_app()
    config = ServerConfig()
    listener = create_mock_listener()
    
    try:
        worker = Worker(app, listener, config, worker_id=5)
        
        stats = worker.get_stats()
        
        if stats["worker_id"] != 5:
            errmsg = f"Expected worker_id 5, got {stats['worker_id']}"
            raise AssertionError(errmsg)
        
        if stats["running"] != False:
            errmsg = f"Expected running False, got {stats['running']}"
            raise AssertionError(errmsg)
        
        if stats["active_connections"] != 0:
            errmsg = f"Expected active_connections 0, got {stats['active_connections']}"
            raise AssertionError(errmsg)
        
        if stats["total_requests"] != 0:
            errmsg = f"Expected total_requests 0, got {stats['total_requests']}"
            raise AssertionError(errmsg)
        
        if "connection_stats" not in stats:
            errmsg = "Expected 'connection_stats' in stats"
            raise AssertionError(errmsg)
    finally:
        listener.close()
    
    return


# ============================================================================
# Tests for Worker Shutdown
# ============================================================================

def test_worker_shutdown_when_not_running():
    """
        Test Worker.shutdown() when worker is not running.
    """
    app = create_simple_app()
    config = ServerConfig()
    listener = create_mock_listener()
    
    try:
        worker = Worker(app, listener, config, worker_id=1)
        
        # Should not raise
        worker.shutdown(graceful=True)
        
        if worker.is_running != False:
            errmsg = f"Expected is_running False, got {worker.is_running}"
            raise AssertionError(errmsg)
    finally:
        listener.close()
    
    return


def test_worker_shutdown_immediate():
    """
        Test Worker.shutdown() with graceful=False.
    """
    app = create_simple_app()
    config = ServerConfig()
    listener = create_mock_listener()
    
    try:
        worker = Worker(app, listener, config, worker_id=1)
        
        # Should not raise
        worker.shutdown(graceful=False)
        
        if worker.is_running != False:
            errmsg = f"Expected is_running False, got {worker.is_running}"
            raise AssertionError(errmsg)
    finally:
        listener.close()
    
    return


# ============================================================================
# Tests for Request Handling Helpers
# ============================================================================

def test_worker_extract_headers_from_environ():
    """
        Test Worker._extract_headers_from_environ() extracts headers correctly.
    """
    app = create_simple_app()
    config = ServerConfig()
    listener = create_mock_listener()
    
    try:
        worker = Worker(app, listener, config)
        
        environ = {
            "HTTP_HOST": "localhost:8000",
            "HTTP_USER_AGENT": "TestClient/1.0",
            "HTTP_ACCEPT": "text/html",
            "CONTENT_TYPE": "application/json",
            "CONTENT_LENGTH": "100",
            "REQUEST_METHOD": "POST",  # Should be ignored
        }
        
        headers = worker._extract_headers_from_environ(environ)
        
        if headers["Host"] != "localhost:8000":
            errmsg = f"Expected Host 'localhost:8000', got '{headers['Host']}'"
            raise AssertionError(errmsg)
        
        if headers["User-Agent"] != "TestClient/1.0":
            errmsg = f"Expected User-Agent 'TestClient/1.0', got '{headers['User-Agent']}'"
            raise AssertionError(errmsg)
        
        if headers["Accept"] != "text/html":
            errmsg = f"Expected Accept 'text/html', got '{headers['Accept']}'"
            raise AssertionError(errmsg)
        
        if headers["Content-Type"] != "application/json":
            errmsg = f"Expected Content-Type 'application/json', got '{headers['Content-Type']}'"
            raise AssertionError(errmsg)
        
        if headers["Content-Length"] != "100":
            errmsg = f"Expected Content-Length '100', got '{headers['Content-Length']}'"
            raise AssertionError(errmsg)
        
        if "Request-Method" in headers:
            errmsg = "Did not expect 'Request-Method' in headers"
            raise AssertionError(errmsg)
    finally:
        listener.close()
    
    return


def test_worker_parse_status_code():
    """
        Test Worker._parse_status_code() parses status correctly.
    """
    app = create_simple_app()
    config = ServerConfig()
    listener = create_mock_listener()
    
    try:
        worker = Worker(app, listener, config)
        
        result = worker._parse_status_code("200 OK")
        if result != 200:
            errmsg = f"Expected 200, got {result}"
            raise AssertionError(errmsg)
        
        result = worker._parse_status_code("404 Not Found")
        if result != 404:
            errmsg = f"Expected 404, got {result}"
            raise AssertionError(errmsg)
        
        result = worker._parse_status_code("500 Internal Server Error")
        if result != 500:
            errmsg = f"Expected 500, got {result}"
            raise AssertionError(errmsg)
        
        result = worker._parse_status_code("201")
        if result != 201:
            errmsg = f"Expected 201, got {result}"
            raise AssertionError(errmsg)
        
        result = worker._parse_status_code("invalid")
        if result != 500:
            errmsg = f"Expected 500 for invalid, got {result}"
            raise AssertionError(errmsg)
        
        result = worker._parse_status_code("")
        if result != 500:
            errmsg = f"Expected 500 for empty, got {result}"
            raise AssertionError(errmsg)
    finally:
        listener.close()
    
    return


# ============================================================================
# Integration Tests for Worker Request Handling
# ============================================================================

def test_worker_handles_simple_request():
    """
        Test Worker handles a simple GET request.
    """
    app = create_simple_app()
    config = ServerConfig(host="127.0.0.1", port=0, keepalive=0)
    listener = create_mock_listener()
    
    # Get actual bound port
    actual_port = listener.socket.getsockname()[1]
    
    try:
        worker = Worker(app, listener, config, worker_id=1)
        
        # Start worker in background thread
        worker_thread = threading.Thread(target=worker.run)
        worker_thread.daemon = True
        worker_thread.start()
        
        # Wait for worker to start
        time.sleep(0.1)
        
        # Send request
        status_code, headers, body = send_http_request(
            "127.0.0.1",
            actual_port,
            method="GET",
            path="/"
        )
        
        if status_code != 200:
            errmsg = f"Expected status 200, got {status_code}"
            raise AssertionError(errmsg)
        
        if body != b"Hello, World!":
            errmsg = f"Expected body b'Hello, World!', got {body}"
            raise AssertionError(errmsg)
        
        # Shutdown worker
        worker.shutdown(graceful=False)
        worker_thread.join(timeout=2.0)
        
        if worker.total_requests != 1:
            errmsg = f"Expected total_requests 1, got {worker.total_requests}"
            raise AssertionError(errmsg)
    finally:
        listener.close()
    
    return


def test_worker_handles_post_request():
    """
        Test Worker handles a POST request with body.
    """
    app = create_echo_app()
    config = ServerConfig(host="127.0.0.1", port=0, keepalive=0)
    listener = create_mock_listener()
    
    # Get actual bound port
    actual_port = listener.socket.getsockname()[1]
    
    try:
        worker = Worker(app, listener, config, worker_id=1)
        
        # Start worker in background thread
        worker_thread = threading.Thread(target=worker.run)
        worker_thread.daemon = True
        worker_thread.start()
        
        # Wait for worker to start
        time.sleep(0.1)
        
        # Send request with body
        request_body = b"Hello from client"
        status_code, headers, body = send_http_request(
            "127.0.0.1",
            actual_port,
            method="POST",
            path="/echo",
            body=request_body
        )
        
        if status_code != 200:
            errmsg = f"Expected status 200, got {status_code}"
            raise AssertionError(errmsg)
        
        if body != request_body:
            errmsg = f"Expected body {request_body}, got {body}"
            raise AssertionError(errmsg)
        
        # Shutdown worker
        worker.shutdown(graceful=False)
        worker_thread.join(timeout=2.0)
    finally:
        listener.close()
    
    return


def test_worker_handles_app_error():
    """
        Test Worker handles application errors gracefully.
    """
    app = create_error_app()
    config = ServerConfig(host="127.0.0.1", port=0, keepalive=0)
    listener = create_mock_listener()
    
    # Get actual bound port
    actual_port = listener.socket.getsockname()[1]
    
    try:
        worker = Worker(app, listener, config, worker_id=1)
        
        # Start worker in background thread
        worker_thread = threading.Thread(target=worker.run)
        worker_thread.daemon = True
        worker_thread.start()
        
        # Wait for worker to start
        time.sleep(0.1)
        
        # Send request
        status_code, headers, body = send_http_request(
            "127.0.0.1",
            actual_port,
            method="GET",
            path="/"
        )
        
        # Should return 500 error
        if status_code != 500:
            errmsg = f"Expected status 500, got {status_code}"
            raise AssertionError(errmsg)
        
        # Shutdown worker
        worker.shutdown(graceful=False)
        worker_thread.join(timeout=2.0)
    finally:
        listener.close()
    
    return


def test_worker_handles_custom_status():
    """
        Test Worker handles custom status codes.
    """
    app = create_status_app(201, "Created")
    config = ServerConfig(host="127.0.0.1", port=0, keepalive=0)
    listener = create_mock_listener()
    
    # Get actual bound port
    actual_port = listener.socket.getsockname()[1]
    
    try:
        worker = Worker(app, listener, config, worker_id=1)
        
        # Start worker in background thread
        worker_thread = threading.Thread(target=worker.run)
        worker_thread.daemon = True
        worker_thread.start()
        
        # Wait for worker to start
        time.sleep(0.1)
        
        # Send request
        status_code, headers, body = send_http_request(
            "127.0.0.1",
            actual_port,
            method="POST",
            path="/create"
        )
        
        if status_code != 201:
            errmsg = f"Expected status 201, got {status_code}"
            raise AssertionError(errmsg)
        
        if body != b"Created":
            errmsg = f"Expected body b'Created', got {body}"
            raise AssertionError(errmsg)
        
        # Shutdown worker
        worker.shutdown(graceful=False)
        worker_thread.join(timeout=2.0)
    finally:
        listener.close()
    
    return
