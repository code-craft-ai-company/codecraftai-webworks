"""
    Tests for the Worker class in the WSGI layer.
    
    This module contains tests for the Worker class which handles HTTP requests
    in the built-in WSGI server.
"""

import logging
import os
import select
import socket
import ssl
import subprocess
import tempfile
import threading
import time
from typing import Any, Callable, Dict, Iterable, List, Tuple

from ccai.errors.exceptions import SkipError

from ccai.testshared.servers.tlscert import create_self_signed_certificate

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


# ============================================================================
# Helpers for tests that talk to a running worker over a raw connection
# ============================================================================

def start_worker(app: Callable, listener: SocketListener = None, **config_values: Any) -> Tuple[Worker, SocketListener, int, threading.Thread]:
    """
        Start a worker on an ephemeral port in a background thread.
        
        :param app: The WSGI application to serve.
        :param listener: Listener to use. If None, one is bound to an ephemeral port.
        :param config_values: ServerConfig values for the worker.
        
        :returns: Tuple of (worker, listener, port, thread).
    """
    if listener is None:
        listener = create_mock_listener()
    
    port = listener.socket.getsockname()[1]
    config = ServerConfig(host="127.0.0.1", port=port, access_log=False, **config_values)
    
    worker = Worker(app, listener, config, worker_id=1)
    worker_thread = threading.Thread(target=worker.run)
    worker_thread.daemon = True
    worker_thread.start()
    
    # Wait for the worker to be inside its accept loop
    deadline = time.time() + 5.0
    while not worker.is_running and time.time() < deadline:
        time.sleep(0.01)
    time.sleep(0.05)
    
    return (worker, listener, port, worker_thread)


def stop_worker(worker: Worker, listener: SocketListener, worker_thread: threading.Thread) -> None:
    """
        Stop a worker started with start_worker and release its listener.
    """
    worker.shutdown(graceful=False)
    worker_thread.join(timeout=5.0)
    listener.close()
    return


def read_until_closed(sock: socket.socket, timeout: float = 5.0) -> bytes:
    """
        Read from a socket until the peer closes it or nothing arrives in time.
    """
    sock.settimeout(timeout)
    data = b""
    
    try:
        while True:
            chunk = sock.recv(65536)
            if len(chunk) == 0:
                break
            data += chunk
    except socket.timeout:
        pass
    
    return data


def raw_exchange(port: int, payload: bytes, half_close: bool = False, timeout: float = 5.0) -> bytes:
    """
        Send raw bytes to the worker and return everything it answers.
        
        :param port: Port of the worker.
        :param payload: Bytes to send.
        :param half_close: If True, close the sending side after the payload.
        :param timeout: Seconds to wait for the worker to close the connection.
        
        :returns: All bytes received.
    """
    sock = socket.create_connection(("127.0.0.1", port))
    
    try:
        if len(payload) > 0:
            sock.sendall(payload)
        if half_close:
            sock.shutdown(socket.SHUT_WR)
        data = read_until_closed(sock, timeout)
    finally:
        sock.close()
    
    return data


GET_CLOSE = b"GET / HTTP/1.1\r\nHost: test\r\nConnection: close\r\n\r\n"
GET_KEEP_ALIVE = b"GET / HTTP/1.1\r\nHost: test\r\n\r\n"


def generator_app(environ: Dict[str, Any], start_response: Callable) -> Iterable[bytes]:
    """
        WSGI application written as a generator: start_response is only
        called when the server asks for the first item.
    """
    start_response("200 OK", [("Content-Type", "text/plain"), ("Content-Length", "5")])
    yield b"hello"


def no_length_app(environ: Dict[str, Any], start_response: Callable) -> Iterable[bytes]:
    """
        WSGI application that streams two items and declares no Content-Length.
    """
    start_response("200 OK", [("Content-Type", "text/plain")])
    yield b"hello "
    yield b"world"


def single_item_app(environ: Dict[str, Any], start_response: Callable) -> Iterable[bytes]:
    """
        WSGI application that returns a list of one item without Content-Length.
    """
    start_response("200 OK", [("Content-Type", "text/plain")])
    return [b"hello"]


# ============================================================================
# Tests for response handling
# ============================================================================

def test_worker_serves_generator_application():
    """
        Test that an application written as a generator is answered with its response.
    """
    worker, listener, port, worker_thread = start_worker(generator_app)
    
    try:
        data = raw_exchange(port, GET_CLOSE)
    finally:
        stop_worker(worker, listener, worker_thread)
    
    if not data.startswith(b"HTTP/1.1 200 OK\r\n"):
        errmsg = f"Expected a 200 response from the generator application, got {data[:80]!r}"
        raise AssertionError(errmsg)
    
    if not data.endswith(b"\r\n\r\nhello"):
        errmsg = f"Expected the body of the generator application, got {data[-40:]!r}"
        raise AssertionError(errmsg)
    
    return


def test_worker_frames_streamed_response_on_keep_alive_connection():
    """
        Test that a response without Content-Length is chunked on a kept-alive connection.
    """
    worker, listener, port, worker_thread = start_worker(no_length_app, keepalive=1)
    
    try:
        data = raw_exchange(port, GET_KEEP_ALIVE)
    finally:
        stop_worker(worker, listener, worker_thread)
    
    head, _, body = data.partition(b"\r\n\r\n")
    
    if b"Transfer-Encoding: chunked" not in head:
        errmsg = f"Expected a chunked response, got headers {head!r}"
        raise AssertionError(errmsg)
    
    if body != b"6\r\nhello \r\n5\r\nworld\r\n0\r\n\r\n":
        errmsg = f"Expected two chunks and the terminating chunk and nothing else, got {body!r}"
        raise AssertionError(errmsg)
    
    return


def test_worker_serves_second_request_after_streamed_response():
    """
        Test that a connection stays usable after a response without Content-Length.
    """
    worker, listener, port, worker_thread = start_worker(no_length_app, keepalive=2)
    
    try:
        sock = socket.create_connection(("127.0.0.1", port))
        try:
            sock.sendall(GET_KEEP_ALIVE)
            time.sleep(0.3)
            sock.sendall(GET_CLOSE)
            data = read_until_closed(sock)
        finally:
            sock.close()
    finally:
        stop_worker(worker, listener, worker_thread)
    
    status_lines = data.count(b"HTTP/1.1 200 OK\r\n")
    
    if status_lines != 2:
        errmsg = f"Expected two 200 responses on one connection, got {status_lines}: {data!r}"
        raise AssertionError(errmsg)
    
    if b"400 Bad Request" in data:
        errmsg = f"Expected no 400 response on the connection, got {data!r}"
        raise AssertionError(errmsg)
    
    return


def test_worker_serves_pipelined_requests():
    """
        Test that two requests sent together are both answered, in order.
    """
    def path_app(environ: Dict[str, Any], start_response: Callable) -> Iterable[bytes]:
        body = environ["PATH_INFO"].encode("ascii")
        start_response("200 OK", [("Content-Length", str(len(body)))])
        return [body]
    
    worker, listener, port, worker_thread = start_worker(path_app, keepalive=2)
    
    payload = (
        b"GET /first HTTP/1.1\r\nHost: test\r\n\r\n"
        b"GET /second HTTP/1.1\r\nHost: test\r\nConnection: close\r\n\r\n"
    )
    
    try:
        data = raw_exchange(port, payload)
    finally:
        stop_worker(worker, listener, worker_thread)
    
    first_pos = data.find(b"/first")
    second_pos = data.find(b"/second")
    
    if first_pos < 0 or second_pos < 0 or first_pos > second_pos:
        errmsg = f"Expected both pipelined requests answered in order, got {data!r}"
        raise AssertionError(errmsg)
    
    return


def test_worker_declares_content_length_for_single_item_body():
    """
        Test that a body of one item gets a Content-Length the application did not set.
    """
    worker, listener, port, worker_thread = start_worker(single_item_app)
    
    try:
        data = raw_exchange(port, GET_CLOSE)
    finally:
        stop_worker(worker, listener, worker_thread)
    
    if b"Content-Length: 5\r\n" not in data:
        errmsg = f"Expected Content-Length: 5, got {data!r}"
        raise AssertionError(errmsg)
    
    return


def test_worker_head_request_gets_no_body():
    """
        Test that the response to a HEAD request ends after the headers.
    """
    worker, listener, port, worker_thread = start_worker(single_item_app)
    
    try:
        data = raw_exchange(port, b"HEAD / HTTP/1.1\r\nHost: test\r\nConnection: close\r\n\r\n")
    finally:
        stop_worker(worker, listener, worker_thread)
    
    if not data.startswith(b"HTTP/1.1 200 OK\r\n"):
        errmsg = f"Expected a 200 response, got {data[:80]!r}"
        raise AssertionError(errmsg)
    
    if not data.endswith(b"\r\n\r\n"):
        errmsg = f"Expected no body in the response to HEAD, got {data!r}"
        raise AssertionError(errmsg)
    
    return


def test_worker_answers_header_injection_with_500():
    """
        Test that a header value with CRLF is not written and the request fails closed.
    """
    def inject_app(environ: Dict[str, Any], start_response: Callable) -> Iterable[bytes]:
        start_response("302 Found", [("Location", "/x\r\nSet-Cookie: sid=evil"), ("Content-Length", "0")])
        return [b""]
    
    worker, listener, port, worker_thread = start_worker(inject_app)
    
    try:
        data = raw_exchange(port, GET_CLOSE)
    finally:
        stop_worker(worker, listener, worker_thread)
    
    if not data.startswith(b"HTTP/1.1 500 "):
        errmsg = f"Expected a 500 response, got {data[:80]!r}"
        raise AssertionError(errmsg)
    
    if b"Set-Cookie" in data:
        errmsg = f"Expected the injected header not to be sent, got {data!r}"
        raise AssertionError(errmsg)
    
    return


def test_worker_does_not_write_second_response_after_late_error():
    """
        Test that an error after the headers were sent does not add a second response.
    """
    def late_error_app(environ: Dict[str, Any], start_response: Callable) -> Iterable[bytes]:
        start_response("200 OK", [("Content-Type", "text/plain"), ("Content-Length", "100")])
        yield b"partial"
        raise RuntimeError("failure after the response has started")
    
    worker, listener, port, worker_thread = start_worker(late_error_app, keepalive=2)
    
    try:
        data = raw_exchange(port, GET_KEEP_ALIVE)
    finally:
        stop_worker(worker, listener, worker_thread)
    
    status_lines = data.count(b"HTTP/1.1 ")
    
    if status_lines != 1:
        errmsg = f"Expected exactly one status line, got {status_lines}: {data!r}"
        raise AssertionError(errmsg)
    
    if not data.endswith(b"partial"):
        errmsg = f"Expected the connection to be closed after the partial body, got {data!r}"
        raise AssertionError(errmsg)
    
    return


def test_worker_stops_application_when_client_disconnects():
    """
        Test that a streaming application is stopped once its client is gone.
    """
    stopped = threading.Event()
    
    def endless_app(environ: Dict[str, Any], start_response: Callable) -> Iterable[bytes]:
        start_response("200 OK", [("Content-Type", "application/octet-stream")])
        try:
            while True:
                yield b"x" * 65536
        finally:
            stopped.set()
    
    worker, listener, port, worker_thread = start_worker(endless_app)
    
    try:
        sock = socket.create_connection(("127.0.0.1", port))
        sock.sendall(GET_KEEP_ALIVE)
        sock.recv(1024)
        sock.close()
        
        was_stopped = stopped.wait(timeout=10.0)
    finally:
        stop_worker(worker, listener, worker_thread)
    
    if not was_stopped:
        errmsg = "Expected the application iterator to be closed after the client disconnected"
        raise AssertionError(errmsg)
    
    return


class AbortedConnectionSocket:
    """
        A client socket whose connection Windows reports as aborted.
        
        Windows often reports a connection the client dropped as WSAECONNABORTED,
        which Python raises as ConnectionAbortedError, rather than as a reset.
    """
    
    def __init__(self, request: bytes, abort_on_recv: bool = False):
        self._request = request
        self._abort_on_recv = abort_on_recv
        self.send_calls = 0
        return
    
    def settimeout(self, value: Any) -> None:
        return
    
    def recv(self, size: int) -> bytes:
        if self._abort_on_recv:
            raise ConnectionAbortedError(10053, "An established connection was aborted by the software in your host machine")
        data = self._request[:size]
        self._request = self._request[size:]
        return data
    
    def send(self, data: bytes) -> int:
        self.send_calls += 1
        raise ConnectionAbortedError(10053, "An established connection was aborted by the software in your host machine")


def test_worker_treats_an_aborted_connection_as_a_lost_client():
    """
        Test that a connection reported as aborted, on reading or writing, is handled as a lost client.
    """
    
    class RecordingHandler(logging.Handler):
        def __init__(self) -> None:
            super().__init__(level=logging.ERROR)
            self.records: List[logging.LogRecord] = []
            return
        
        def emit(self, record: logging.LogRecord) -> None:
            self.records.append(record)
            return
    
    calls: List[str] = []
    listener = create_mock_listener()
    config = ServerConfig(host="127.0.0.1", port=listener.socket.getsockname()[1], access_log=False)
    worker = Worker(create_recording_app(calls), listener, config, worker_id=1)
    
    handler = RecordingHandler()
    worker_logger = logging.getLogger("webworks.wsgi.worker")
    worker_logger.addHandler(handler)
    
    try:
        # Aborted while the response is written
        writing_sock = AbortedConnectionSocket(GET_CLOSE)
        keep_alive_after_write = worker.handle_request(writing_sock, ("127.0.0.1", 50000))
        
        # Aborted while the request is read
        reading_sock = AbortedConnectionSocket(b"", abort_on_recv=True)
        keep_alive_after_read = worker.handle_request(reading_sock, ("127.0.0.1", 50001))
    finally:
        worker_logger.removeHandler(handler)
        listener.close()
    
    if calls != ["/"]:
        errmsg = f"Expected the application to be called once, for the request that was read, got {calls}"
        raise AssertionError(errmsg)
    
    if keep_alive_after_write or keep_alive_after_read:
        errmsg = "Expected an aborted connection not to be kept alive"
        raise AssertionError(errmsg)
    
    if writing_sock.send_calls != 1:
        errmsg = f"Expected no error response to be written after the abort, got {writing_sock.send_calls} writes"
        raise AssertionError(errmsg)
    
    errors = [record.getMessage() for record in handler.records]
    if len(errors) != 0:
        errmsg = f"Expected an aborted connection to be handled without an error, got {errors}"
        raise AssertionError(errmsg)
    
    return


# ============================================================================
# Tests for requests that must not reach the application
# ============================================================================

def create_recording_app(calls: List[str]) -> Callable:
    """
        Create a WSGI application that records the path of every request it gets.
    """
    def app(environ: Dict[str, Any], start_response: Callable) -> Iterable[bytes]:
        calls.append(environ["PATH_INFO"])
        start_response("200 OK", [("Content-Length", "2")])
        return [b"ok"]
    
    return app


def test_worker_refuses_truncated_body_without_calling_application():
    """
        Test that a request whose body was cut short is answered with 400 and not dispatched.
    """
    calls: List[str] = []
    worker, listener, port, worker_thread = start_worker(create_recording_app(calls))
    
    payload = b"POST /upload HTTP/1.1\r\nHost: test\r\nContent-Length: 100\r\n\r\nshort"
    
    try:
        data = raw_exchange(port, payload, half_close=True)
    finally:
        stop_worker(worker, listener, worker_thread)
    
    if not data.startswith(b"HTTP/1.1 400 "):
        errmsg = f"Expected a 400 response, got {data[:80]!r}"
        raise AssertionError(errmsg)
    
    if len(calls) != 0:
        errmsg = f"Expected the application not to be called, it was called for {calls}"
        raise AssertionError(errmsg)
    
    return


def test_worker_closes_unused_connection_without_response():
    """
        Test that a client that connects and closes without a request gets no response.
    """
    calls: List[str] = []
    worker, listener, port, worker_thread = start_worker(create_recording_app(calls))
    
    try:
        data = raw_exchange(port, b"", half_close=True)
    finally:
        stop_worker(worker, listener, worker_thread)
    
    if len(data) != 0:
        errmsg = f"Expected no response on an unused connection, got {data!r}"
        raise AssertionError(errmsg)
    
    return


def test_worker_closes_idle_keep_alive_connection_without_response():
    """
        Test that a keep-alive connection that idles out is closed without a 400.
    """
    calls: List[str] = []
    worker, listener, port, worker_thread = start_worker(create_recording_app(calls), keepalive=1)
    
    try:
        data = raw_exchange(port, GET_KEEP_ALIVE, timeout=6.0)
    finally:
        stop_worker(worker, listener, worker_thread)
    
    status_lines = data.count(b"HTTP/1.1 ")
    
    if status_lines != 1 or not data.endswith(b"ok"):
        errmsg = f"Expected one response and a silent close, got {data!r}"
        raise AssertionError(errmsg)
    
    return


def test_worker_answers_stalled_headers_with_408():
    """
        Test that a client that stalls inside the headers is answered with 408.
    """
    calls: List[str] = []
    worker, listener, port, worker_thread = start_worker(create_recording_app(calls), timeout=1)
    
    try:
        data = raw_exchange(port, b"GET / HTTP/1.1\r\nHost: te", timeout=6.0)
    finally:
        stop_worker(worker, listener, worker_thread)
    
    if not data.startswith(b"HTTP/1.1 408 "):
        errmsg = f"Expected a 408 response, got {data[:80]!r}"
        raise AssertionError(errmsg)
    
    if len(calls) != 0:
        errmsg = f"Expected the application not to be called, it was called for {calls}"
        raise AssertionError(errmsg)
    
    return


def test_worker_bounds_slowly_dripped_headers_with_deadline():
    """
        Test that a client sending a byte at a time cannot keep the header read open.
    """
    calls: List[str] = []
    worker, listener, port, worker_thread = start_worker(create_recording_app(calls), timeout=1)

    data = b""
    answered_while_sending = False

    # Dripping all of it takes about 5.5 seconds, far past the 1 second deadline
    dripped = b"GET / HTTP/1.1\r\nX-Slow: aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"

    try:
        sock = socket.create_connection(("127.0.0.1", port))
        try:
            # Each byte arrives well within the timeout of a single read
            for byte in dripped:
                # Stop sending once the server has answered, as a client
                # does. Writing to a connection the server has closed draws a
                # reset, and on macOS and Windows the reset discards the
                # answer before the client reads it.
                readable, _, _ = select.select([sock], [], [], 0)
                if len(readable) > 0:
                    answered_while_sending = True
                    break

                try:
                    sock.sendall(bytes([byte]))
                except OSError:
                    break
                time.sleep(0.1)
            data = read_until_closed(sock, timeout=3.0)
        finally:
            sock.close()
    finally:
        stop_worker(worker, listener, worker_thread)

    if not data.startswith(b"HTTP/1.1 408 "):
        errmsg = f"Expected the dripping client to be cut off with 408, got {data[:80]!r}"
        raise AssertionError(errmsg)

    # A 408 that arrives only after the last byte would come from the
    # timeout of a single read, not from the deadline on the headers
    if not answered_while_sending:
        errmsg = "Expected the 408 to arrive while the client was still sending"
        raise AssertionError(errmsg)

    return


def test_worker_answers_oversized_body_with_413():
    """
        Test that a body over the configured limit is answered with 413.
    """
    calls: List[str] = []
    worker, listener, port, worker_thread = start_worker(create_recording_app(calls), max_request_size=10)
    
    payload = b"POST / HTTP/1.1\r\nHost: test\r\nContent-Length: 20\r\n\r\n" + b"a" * 20
    
    try:
        data = raw_exchange(port, payload)
    finally:
        stop_worker(worker, listener, worker_thread)
    
    if not data.startswith(b"HTTP/1.1 413 "):
        errmsg = f"Expected a 413 response, got {data[:80]!r}"
        raise AssertionError(errmsg)
    
    return


def test_worker_answers_long_request_line_with_414():
    """
        Test that a request line over the configured limit is answered with 414.
    """
    calls: List[str] = []
    worker, listener, port, worker_thread = start_worker(create_recording_app(calls), max_request_line=256)
    
    payload = b"GET /" + b"a" * 5000 + b" HTTP/1.1\r\nHost: test\r\n\r\n"
    
    try:
        data = raw_exchange(port, payload)
    finally:
        stop_worker(worker, listener, worker_thread)
    
    if not data.startswith(b"HTTP/1.1 414 "):
        errmsg = f"Expected a 414 response, got {data[:80]!r}"
        raise AssertionError(errmsg)
    
    return


def test_worker_answers_large_headers_with_431():
    """
        Test that headers over the configured limit are answered with 431.
    """
    calls: List[str] = []
    worker, listener, port, worker_thread = start_worker(create_recording_app(calls), max_header_size=512)
    
    payload = b"GET / HTTP/1.1\r\nHost: test\r\nX-Big: " + b"a" * 5000 + b"\r\n\r\n"
    
    try:
        data = raw_exchange(port, payload)
    finally:
        stop_worker(worker, listener, worker_thread)
    
    if not data.startswith(b"HTTP/1.1 431 "):
        errmsg = f"Expected a 431 response, got {data[:80]!r}"
        raise AssertionError(errmsg)
    
    return


# ============================================================================
# Tests for concurrency and shutdown
# ============================================================================

def test_worker_silent_client_does_not_block_other_clients():
    """
        Test that a client that connects and sends nothing does not stop others being served.
    """
    calls: List[str] = []
    worker, listener, port, worker_thread = start_worker(create_recording_app(calls), threads=1, timeout=20)
    
    try:
        silent = socket.create_connection(("127.0.0.1", port))
        try:
            time.sleep(0.2)
            started = time.time()
            data = raw_exchange(port, GET_CLOSE)
            elapsed = time.time() - started
        finally:
            silent.close()
    finally:
        stop_worker(worker, listener, worker_thread)
    
    if not data.startswith(b"HTTP/1.1 200 "):
        errmsg = f"Expected a 200 response, got {data[:80]!r}"
        raise AssertionError(errmsg)
    
    if elapsed > 5.0:
        errmsg = f"Expected the second client to be served at once, it waited {elapsed:.1f}s"
        raise AssertionError(errmsg)
    
    return


def test_worker_idle_keep_alive_client_does_not_block_other_clients():
    """
        Test that a client idling on a kept-alive connection does not stop others being served.
    """
    calls: List[str] = []
    worker, listener, port, worker_thread = start_worker(create_recording_app(calls), threads=1, keepalive=20)
    
    try:
        idle = socket.create_connection(("127.0.0.1", port))
        try:
            idle.sendall(GET_KEEP_ALIVE)
            idle.settimeout(5.0)
            idle.recv(4096)
            
            started = time.time()
            data = raw_exchange(port, GET_CLOSE)
            elapsed = time.time() - started
        finally:
            idle.close()
    finally:
        stop_worker(worker, listener, worker_thread)
    
    if not data.startswith(b"HTTP/1.1 200 "):
        errmsg = f"Expected a 200 response, got {data[:80]!r}"
        raise AssertionError(errmsg)
    
    if elapsed > 5.0:
        errmsg = f"Expected the second client to be served at once, it waited {elapsed:.1f}s"
        raise AssertionError(errmsg)
    
    return


def test_worker_honours_threads_for_sync_worker_class():
    """
        Test that 'threads' handler threads serve requests side by side for the sync worker class.
    """
    both_inside = threading.Barrier(2, timeout=5.0)
    outcomes: List[str] = []
    
    def meeting_app(environ: Dict[str, Any], start_response: Callable) -> Iterable[bytes]:
        # Two requests can only meet here when they are served at the same time
        try:
            both_inside.wait()
            body = b"met"
        except threading.BrokenBarrierError:
            body = b"alone"
        start_response("200 OK", [("Content-Length", str(len(body)))])
        return [body]
    
    def client() -> None:
        data = raw_exchange(port, GET_CLOSE, timeout=10.0)
        outcomes.append(data.rpartition(b"\r\n\r\n")[2].decode("ascii"))
        return
    
    worker, listener, port, worker_thread = start_worker(meeting_app, threads=2, worker_class="sync")
    
    try:
        clients = [threading.Thread(target=client) for _ in range(2)]
        for client_thread in clients:
            client_thread.start()
        for client_thread in clients:
            client_thread.join(timeout=15.0)
    finally:
        stop_worker(worker, listener, worker_thread)
    
    if outcomes != ["met", "met"]:
        errmsg = f"Expected both requests to be served at the same time, got {outcomes}"
        raise AssertionError(errmsg)
    
    return


def test_worker_request_shutdown_returns_without_waiting():
    """
        Test that request_shutdown only records the request, as a signal handler needs.
    """
    release = threading.Event()
    entered = threading.Event()
    
    def blocking_app(environ: Dict[str, Any], start_response: Callable) -> Iterable[bytes]:
        entered.set()
        release.wait(timeout=10.0)
        start_response("200 OK", [("Content-Length", "2")])
        return [b"ok"]
    
    worker, listener, port, worker_thread = start_worker(blocking_app, graceful_timeout=10)
    
    try:
        client = threading.Thread(target=raw_exchange, args=(port, GET_CLOSE))
        client.start()
        entered.wait(timeout=5.0)
        
        started = time.time()
        worker.request_shutdown(graceful=True)
        elapsed = time.time() - started
        
        release.set()
        client.join(timeout=10.0)
        worker_thread.join(timeout=10.0)
    finally:
        release.set()
        listener.close()
    
    if elapsed > 1.0:
        errmsg = f"Expected request_shutdown to return at once, it took {elapsed:.1f}s"
        raise AssertionError(errmsg)
    
    return


def test_worker_graceful_shutdown_finishes_request_in_flight():
    """
        Test that a request being served when a graceful shutdown is requested gets its response.
    """
    release = threading.Event()
    entered = threading.Event()
    responses: List[bytes] = []
    
    def blocking_app(environ: Dict[str, Any], start_response: Callable) -> Iterable[bytes]:
        entered.set()
        release.wait(timeout=10.0)
        start_response("200 OK", [("Content-Length", "8")])
        return [b"finished"]
    
    def client() -> None:
        responses.append(raw_exchange(port, GET_CLOSE, timeout=10.0))
        return
    
    worker, listener, port, worker_thread = start_worker(blocking_app, graceful_timeout=10)
    
    try:
        client_thread = threading.Thread(target=client)
        client_thread.start()
        entered.wait(timeout=5.0)
        
        worker.request_shutdown(graceful=True)
        time.sleep(0.3)
        release.set()
        
        client_thread.join(timeout=10.0)
        worker_thread.join(timeout=10.0)
    finally:
        release.set()
        listener.close()
    
    if len(responses) != 1 or not responses[0].endswith(b"finished"):
        errmsg = f"Expected the request in flight to be answered, got {responses!r}"
        raise AssertionError(errmsg)
    
    if worker.is_running is not False:
        errmsg = "Expected the worker to have stopped after the request finished"
        raise AssertionError(errmsg)
    
    return


def test_worker_silent_tls_client_does_not_block_other_clients():
    """
        Test that a client that never starts the TLS handshake does not stop others being served.
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        certfile = os.path.join(tmpdir, "cert.pem")
        keyfile = os.path.join(tmpdir, "key.pem")
        
        try:
            subprocess.run(
                [
                    "openssl", "req", "-x509", "-newkey", "rsa:2048",
                    "-keyout", keyfile, "-out", certfile,
                    "-days", "1", "-nodes", "-subj", "/CN=localhost",
                ],
                check=True,
                capture_output=True,
            )
        except (OSError, subprocess.CalledProcessError) as openssl_err:
            raise SkipError(f"The openssl command is needed to create a test certificate: {openssl_err}")
        
        listener_config = ServerConfig(host="127.0.0.1", port=0, ssl_certfile=certfile, ssl_keyfile=keyfile)
        tls_listener = SocketListener(listener_config)
        tls_listener.bind()
        tls_listener.setup_ssl()
        
        calls: List[str] = []
        worker, listener, port, worker_thread = start_worker(
            create_recording_app(calls),
            listener=tls_listener,
            threads=1,
            timeout=20
        )
        
        try:
            silent = socket.create_connection(("127.0.0.1", port))
            try:
                time.sleep(0.2)
                
                client_context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
                client_context.check_hostname = False
                client_context.verify_mode = ssl.CERT_NONE
                
                started = time.time()
                raw_sock = socket.create_connection(("127.0.0.1", port), timeout=10.0)
                tls_sock = client_context.wrap_socket(raw_sock)
                try:
                    tls_sock.sendall(GET_CLOSE)
                    data = read_until_closed(tls_sock, timeout=10.0)
                finally:
                    tls_sock.close()
                elapsed = time.time() - started
            finally:
                silent.close()
        finally:
            stop_worker(worker, listener, worker_thread)
    
    if not data.startswith(b"HTTP/1.1 200 "):
        errmsg = f"Expected a 200 response over TLS, got {data[:80]!r}"
        raise AssertionError(errmsg)
    
    if elapsed > 8.0:
        errmsg = f"Expected the TLS client to be served at once, it waited {elapsed:.1f}s"
        raise AssertionError(errmsg)

    return


def test_worker_forced_stop_ends_a_queued_tls_handshake_cleanly():
    """
        Test that a TLS connection queued for a handler thread at a forced stop ends as a closed connection.
    """
    
    class RecordingHandler(logging.Handler):
        def __init__(self) -> None:
            super().__init__(level=logging.ERROR)
            self.records: List[logging.LogRecord] = []
            return
        
        def emit(self, record: logging.LogRecord) -> None:
            self.records.append(record)
            return
    
    app_entered = threading.Event()
    release_app = threading.Event()
    
    def blocking_app(environ: Dict[str, Any], start_response: Callable) -> Iterable[bytes]:
        app_entered.set()
        release_app.wait(timeout=10.0)
        start_response("200 OK", [("Content-Type", "text/plain")])
        return [b"ok"]
    
    handler = RecordingHandler()
    worker_logger = logging.getLogger("webworks.wsgi.worker")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        certfile, keyfile = create_self_signed_certificate(tmpdir)
        
        listener_config = ServerConfig(host="127.0.0.1", port=0, ssl_certfile=certfile, ssl_keyfile=keyfile)
        tls_listener = SocketListener(listener_config)
        tls_listener.bind()
        tls_listener.setup_ssl()
        
        worker, listener, port, worker_thread = start_worker(
            blocking_app,
            listener=tls_listener,
            threads=1,
            timeout=20
        )
        
        worker_logger.addHandler(handler)
        
        busy_client = None
        queued_client = None
        
        try:
            # The only handler thread is held inside the application
            client_context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
            client_context.check_hostname = False
            client_context.verify_mode = ssl.CERT_NONE
            raw_sock = socket.create_connection(("127.0.0.1", port), timeout=10.0)
            busy_client = client_context.wrap_socket(raw_sock)
            busy_client.sendall(GET_CLOSE)
            
            if not app_entered.wait(timeout=5.0):
                errmsg = "Expected the first request to reach the application"
                raise AssertionError(errmsg)
            
            # The first byte of a TLS record makes the second connection
            # readable, so it is queued for the handler thread with its
            # handshake still to be done
            queued_client = socket.create_connection(("127.0.0.1", port))
            queued_client.sendall(b"\x16")
            
            deadline = time.time() + 5.0
            while len(worker._serving) < 2 and time.time() < deadline:
                time.sleep(0.01)
            
            if len(worker._serving) < 2:
                errmsg = "Expected the second connection to be queued for the handler thread"
                raise AssertionError(errmsg)
            
            stop_worker(worker, listener, worker_thread)
            
            # The handler thread finishes the first request and then starts
            # the handshake of the queued connection, whose socket the stop
            # has shut down
            release_app.set()
            
            deadline = time.time() + 5.0
            while len(worker._serving) > 0 and time.time() < deadline:
                time.sleep(0.01)
        finally:
            release_app.set()
            worker_logger.removeHandler(handler)
            for client in (busy_client, queued_client):
                if client is not None:
                    client.close()
    
    if len(worker._serving) != 0:
        errmsg = "Expected the handler thread to end both connections after the stop"
        raise AssertionError(errmsg)
    
    errors = [record.getMessage() for record in handler.records]
    if len(errors) != 0:
        errmsg = f"Expected the stopped connections to end without an error, got {errors}"
        raise AssertionError(errmsg)
    
    return


class LifecycleApp:
    """
        A WSGI application that takes part in the life of the worker.
    """
    
    def __init__(self, fail_start: bool = False):
        self.events: List[str] = []
        self.fail_start = fail_start
        return
    
    def on_worker_start(self, worker: Worker) -> None:
        self.events.append(f"start {worker.worker_id}")
        if self.fail_start:
            raise RuntimeError("the application cannot start")
        return
    
    def on_worker_exit(self, worker: Worker) -> None:
        self.events.append(f"exit {worker.worker_id}")
        return
    
    def __call__(self, environ: Dict[str, Any], start_response: Callable) -> Iterable[bytes]:
        self.events.append("request")
        start_response("200 OK", [("Content-Length", "2")])
        return [b"ok"]


def test_worker_calls_application_lifecycle_methods():
    """
        on_worker_start runs before the first request, on_worker_exit after the last.
    """
    app = LifecycleApp()
    worker, listener, port, worker_thread = start_worker(app)
    
    try:
        response = raw_exchange(port, GET_CLOSE)
    finally:
        stop_worker(worker, listener, worker_thread)
    
    if not response.endswith(b"ok"):
        errmsg = f"Expected the request to be served, got {response!r}"
        raise AssertionError(errmsg)
    
    if app.events != ["start 1", "request", "exit 1"]:
        errmsg = f"Expected start, request, exit, got {app.events}"
        raise AssertionError(errmsg)
    
    return


def test_worker_that_cannot_start_the_application_raises_boot_error():
    """
        An exception from on_worker_start is a WorkerBootError and nothing is served.
    """
    from ccai.webworks.wsgi.exceptions import WorkerBootError
    
    app = LifecycleApp(fail_start=True)
    listener = create_mock_listener()
    port = listener.socket.getsockname()[1]
    worker = Worker(app, listener, ServerConfig(host="127.0.0.1", port=port, access_log=False), worker_id=7)
    
    try:
        worker.run()
    except WorkerBootError as boot_err:
        if boot_err.worker_id != 7 or "cannot start" not in str(boot_err):
            errmsg = f"Expected the boot error of worker 7 with the cause, got {boot_err}"
            raise AssertionError(errmsg)
    else:
        errmsg = "Expected WorkerBootError from run()"
        raise AssertionError(errmsg)
    finally:
        listener.close()
    
    if worker.is_running is not False or app.events != ["start 7"]:
        errmsg = f"Expected the worker not to run and not to stop the application, got {app.events}"
        raise AssertionError(errmsg)
    
    return


def test_worker_recycles_itself_after_max_requests():
    """
        After max_requests requests the worker stops; the last response says Connection: close.
    """
    worker, listener, port, worker_thread = start_worker(create_simple_app(), max_requests=3, graceful_timeout=5)
    responses: List[bytes] = []
    
    try:
        for _ in range(3):
            responses.append(raw_exchange(port, GET_KEEP_ALIVE, half_close=True))
        worker_thread.join(timeout=10.0)
        stopped = not worker_thread.is_alive()
    finally:
        stop_worker(worker, listener, worker_thread)
    
    if len(responses) != 3 or not all(response.startswith(b"HTTP/1.1 200") for response in responses):
        errmsg = f"Expected three 200 responses, got {responses!r}"
        raise AssertionError(errmsg)
    
    if b"Connection: keep-alive" not in responses[0] or b"Connection: close" not in responses[2]:
        errmsg = f"Expected the last response to close the connection, got {responses!r}"
        raise AssertionError(errmsg)
    
    if not stopped or worker.total_requests != 3:
        errmsg = f"Expected the worker to stop after 3 requests, stopped={stopped}, requests={worker.total_requests}"
        raise AssertionError(errmsg)
    
    return


def test_worker_max_requests_limit_includes_jitter():
    """
        The limit is max_requests plus a random 0..max_requests_jitter.
    """
    listener = create_mock_listener()
    
    try:
        limits = set()
        for _ in range(30):
            config = ServerConfig(host="127.0.0.1", port=0, max_requests=100, max_requests_jitter=5)
            limits.add(Worker(create_simple_app(), listener, config).max_requests_limit)
        unlimited = Worker(create_simple_app(), listener, ServerConfig(host="127.0.0.1", port=0)).max_requests_limit
    finally:
        listener.close()
    
    if not limits.issubset(set(range(100, 106))) or len(limits) < 2:
        errmsg = f"Expected limits between 100 and 105 that vary, got {sorted(limits)}"
        raise AssertionError(errmsg)
    
    if unlimited is not None:
        errmsg = f"Expected no limit without max_requests, got {unlimited}"
        raise AssertionError(errmsg)
    
    return


def test_worker_graceful_shutdown_serves_accepted_connection():
    """
        A connection accepted before a graceful shutdown gets its first request served.
    """
    responses: List[bytes] = []
    worker, listener, port, worker_thread = start_worker(create_simple_app(), graceful_timeout=5)
    
    try:
        client_sock = socket.create_connection(("127.0.0.1", port))
        # Give the accept loop the time to accept the silent connection
        deadline = time.time() + 5.0
        while worker.get_stats()["connection_stats"].get("total_connections", 0) < 1 and time.time() < deadline:
            time.sleep(0.01)
        
        worker.request_shutdown(graceful=True)
        client_sock.sendall(GET_CLOSE)
        responses.append(read_until_closed(client_sock, timeout=5.0))
        client_sock.close()
        worker_thread.join(timeout=10.0)
    finally:
        stop_worker(worker, listener, worker_thread)
    
    if len(responses) != 1 or not responses[0].startswith(b"HTTP/1.1 200"):
        errmsg = f"Expected the accepted connection to be answered, got {responses!r}"
        raise AssertionError(errmsg)
    
    return
