"""
    Tests for the SocketListener class.
    
    This module contains unit tests for the WSGI socket listener functionality
    including binding to IPv4, IPv6, and Unix domain sockets, socket options
    configuration, connection acceptance, and SSL/TLS support.
"""

import os
import socket as socket_module
import tempfile
import threading
from typing import Optional

from ccai.errors.exceptions import SkipError
from ccai.webworks.wsgi.socketlistener import SocketListener
from ccai.webworks.wsgi.serverconfig import ServerConfig
from ccai.webworks.wsgi.exceptions import BindError


# =============================================================================
# Helper Functions
# =============================================================================

def find_available_port() -> int:
    """
        Find an available port for testing.
        
        :returns: Available port number.
    """
    with socket_module.socket(socket_module.AF_INET, socket_module.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        port = sock.getsockname()[1]
    return port


def _require_unix_sockets() -> None:
    """
        Skip the calling test on platforms whose socket module has no AF_UNIX.

        :raises SkipError: When Unix domain sockets are unavailable (Windows).
    """
    if not hasattr(socket_module, "AF_UNIX"):
        raise SkipError("Unix domain sockets (AF_UNIX) are not available on this platform")
    return


# =============================================================================
# Unit Tests for SocketListener Construction
# =============================================================================

def test_socketlistener_construction():
    """
        Test that SocketListener can be constructed with ServerConfig.
    """
    config = ServerConfig()
    listener = SocketListener(config)
    
    if listener.config is not config:
        errmsg = "Expected config to be the same instance"
        raise AssertionError(errmsg)
    
    if listener.socket is not None:
        errmsg = "Expected socket to be None before bind"
        raise AssertionError(errmsg)
    
    if listener.is_unix_socket is not False:
        errmsg = "Expected is_unix_socket to be False initially"
        raise AssertionError(errmsg)
    
    if listener.bound_address is not None:
        errmsg = "Expected bound_address to be None before bind"
        raise AssertionError(errmsg)
    
    return


def test_socketlistener_config_property():
    """
        Test that config property returns the configuration.
    """
    config = ServerConfig(host="0.0.0.0", port=9000)
    listener = SocketListener(config)
    
    if listener.config.host != "0.0.0.0":
        errmsg = f"Expected host '0.0.0.0', got '{listener.config.host}'"
        raise AssertionError(errmsg)
    
    if listener.config.port != 9000:
        errmsg = f"Expected port 9000, got {listener.config.port}"
        raise AssertionError(errmsg)
    
    return


# =============================================================================
# Unit Tests for IPv4 Binding
# =============================================================================

def test_bind_ipv4_localhost():
    """
        Test binding to IPv4 localhost address.
    """
    port = find_available_port()
    config = ServerConfig(host="127.0.0.1", port=port)
    listener = SocketListener(config)
    
    try:
        listener.bind()
        
        if listener.socket is None:
            errmsg = "Expected socket to be set after bind"
            raise AssertionError(errmsg)
        
        if listener.is_unix_socket is not False:
            errmsg = "Expected is_unix_socket to be False for TCP"
            raise AssertionError(errmsg)
        
        expected_address = f"127.0.0.1:{port}"
        if listener.bound_address != expected_address:
            errmsg = f"Expected bound_address '{expected_address}', got '{listener.bound_address}'"
            raise AssertionError(errmsg)
    finally:
        listener.close()
    
    return


def test_bind_ipv4_all_interfaces():
    """
        Test binding to all IPv4 interfaces.
    """
    port = find_available_port()
    config = ServerConfig(host="0.0.0.0", port=port)
    listener = SocketListener(config)
    
    try:
        listener.bind()
        
        if listener.socket is None:
            errmsg = "Expected socket to be set after bind"
            raise AssertionError(errmsg)
        
        expected_address = f"0.0.0.0:{port}"
        if listener.bound_address != expected_address:
            errmsg = f"Expected bound_address '{expected_address}', got '{listener.bound_address}'"
            raise AssertionError(errmsg)
    finally:
        listener.close()
    
    return


# =============================================================================
# Unit Tests for IPv6 Binding
# =============================================================================

def test_bind_ipv6_localhost():
    """
        Test binding to IPv6 localhost address.
    """
    port = find_available_port()
    config = ServerConfig(host="::1", port=port)
    listener = SocketListener(config)
    
    try:
        listener.bind()
        
        if listener.socket is None:
            errmsg = "Expected socket to be set after bind"
            raise AssertionError(errmsg)
        
        if listener.is_unix_socket is not False:
            errmsg = "Expected is_unix_socket to be False for TCP"
            raise AssertionError(errmsg)
        
        expected_address = f"::1:{port}"
        if listener.bound_address != expected_address:
            errmsg = f"Expected bound_address '{expected_address}', got '{listener.bound_address}'"
            raise AssertionError(errmsg)
    finally:
        listener.close()
    
    return


# =============================================================================
# Unit Tests for Unix Domain Socket Binding
# =============================================================================

def test_bind_unix_socket():
    """
        Test binding to a Unix domain socket.
    """
    _require_unix_sockets()

    with tempfile.TemporaryDirectory() as temp_dir:
        socket_path = os.path.join(temp_dir, "test.sock")
        config = ServerConfig(unix_socket=socket_path)
        listener = SocketListener(config)
        
        try:
            listener.bind()
            
            if listener.socket is None:
                errmsg = "Expected socket to be set after bind"
                raise AssertionError(errmsg)
            
            if listener.is_unix_socket is not True:
                errmsg = "Expected is_unix_socket to be True for Unix socket"
                raise AssertionError(errmsg)
            
            if listener.bound_address != socket_path:
                errmsg = f"Expected bound_address '{socket_path}', got '{listener.bound_address}'"
                raise AssertionError(errmsg)
            
            # Verify socket file exists
            if os.path.exists(socket_path) is not True:
                errmsg = "Expected socket file to exist"
                raise AssertionError(errmsg)
        finally:
            listener.close()
    
    return


def test_bind_unix_socket_removes_existing():
    """
        Test that binding removes existing socket file.
    """
    _require_unix_sockets()

    with tempfile.TemporaryDirectory() as temp_dir:
        socket_path = os.path.join(temp_dir, "test.sock")
        
        # Create an existing file at the socket path
        with open(socket_path, "w") as f:
            f.write("dummy")
        
        config = ServerConfig(unix_socket=socket_path)
        listener = SocketListener(config)
        
        try:
            listener.bind()
            
            if listener.socket is None:
                errmsg = "Expected socket to be set after bind"
                raise AssertionError(errmsg)
        finally:
            listener.close()
    
    return


# =============================================================================
# Unit Tests for Socket Options
# =============================================================================

def test_socket_options_reuseaddr():
    """
        Test that SO_REUSEADDR is set on the socket.
    """
    port = find_available_port()
    config = ServerConfig(host="127.0.0.1", port=port)
    listener = SocketListener(config)
    
    try:
        listener.bind()
        
        reuseaddr = listener.socket.getsockopt(socket_module.SOL_SOCKET, socket_module.SO_REUSEADDR)
        if reuseaddr == 0:
            errmsg = "Expected SO_REUSEADDR to be set"
            raise AssertionError(errmsg)
    finally:
        listener.close()
    
    return


def test_socket_backlog_configuration():
    """
        Test that backlog is configured correctly.
    """
    port = find_available_port()
    config = ServerConfig(host="127.0.0.1", port=port, backlog=128)
    listener = SocketListener(config)
    
    try:
        listener.bind()
        
        # We can't directly verify backlog, but we can verify the socket is listening
        if listener.socket is None:
            errmsg = "Expected socket to be set after bind"
            raise AssertionError(errmsg)
    finally:
        listener.close()
    
    return


# =============================================================================
# Unit Tests for accept() Method
# =============================================================================

def test_accept_returns_client_socket():
    """
        Test that accept returns a client socket and address.
    """
    port = find_available_port()
    config = ServerConfig(host="127.0.0.1", port=port)
    listener = SocketListener(config)
    
    try:
        listener.bind()
        
        # Create a client connection in a separate thread
        client_connected = threading.Event()
        client_socket: Optional[socket_module.socket] = None
        
        def connect_client():
            nonlocal client_socket
            client_socket = socket_module.socket(socket_module.AF_INET, socket_module.SOCK_STREAM)
            client_socket.connect(("127.0.0.1", port))
            client_connected.set()
            return
        
        client_thread = threading.Thread(target=connect_client)
        client_thread.start()
        
        # Accept the connection
        accepted_sock, client_addr = listener.accept()
        
        client_connected.wait(timeout=5)
        client_thread.join(timeout=5)
        
        if accepted_sock is None:
            errmsg = "Expected accepted socket to not be None"
            raise AssertionError(errmsg)
        
        if client_addr[0] != "127.0.0.1":
            errmsg = f"Expected client address '127.0.0.1', got '{client_addr[0]}'"
            raise AssertionError(errmsg)
        
        # Clean up
        accepted_sock.close()
        if client_socket is not None:
            client_socket.close()
    finally:
        listener.close()
    
    return


def test_accept_raises_when_not_bound():
    """
        Test that accept raises RuntimeError when socket is not bound.
    """
    config = ServerConfig()
    listener = SocketListener(config)
    
    exception_raised = False
    
    try:
        listener.accept()
    except RuntimeError as err:
        exception_raised = True
        if "not bound" not in str(err).lower():
            errmsg = f"Expected 'not bound' in error message, got '{err}'"
            raise AssertionError(errmsg)
    
    if exception_raised is not True:
        errmsg = "Expected RuntimeError to be raised"
        raise AssertionError(errmsg)
    
    return


def test_accept_unix_socket_returns_empty_address():
    """
        Test that accept on Unix socket returns empty address tuple.
    """
    _require_unix_sockets()

    with tempfile.TemporaryDirectory() as temp_dir:
        socket_path = os.path.join(temp_dir, "test.sock")
        config = ServerConfig(unix_socket=socket_path)
        listener = SocketListener(config)
        
        try:
            listener.bind()
            
            # Create a client connection in a separate thread
            client_socket: Optional[socket_module.socket] = None
            
            def connect_client():
                nonlocal client_socket
                client_socket = socket_module.socket(socket_module.AF_UNIX, socket_module.SOCK_STREAM)
                client_socket.connect(socket_path)
                return
            
            client_thread = threading.Thread(target=connect_client)
            client_thread.start()
            
            # Accept the connection
            accepted_sock, client_addr = listener.accept()
            
            client_thread.join(timeout=5)
            
            # Unix sockets should return ("", 0) for address
            if client_addr != ("", 0):
                errmsg = f"Expected client address ('', 0), got {client_addr}"
                raise AssertionError(errmsg)
            
            # Clean up
            accepted_sock.close()
            if client_socket is not None:
                client_socket.close()
        finally:
            listener.close()
    
    return


# =============================================================================
# Unit Tests for close() Method
# =============================================================================

def test_close_releases_socket():
    """
        Test that close releases the socket.
    """
    port = find_available_port()
    config = ServerConfig(host="127.0.0.1", port=port)
    listener = SocketListener(config)
    
    listener.bind()
    
    if listener.socket is None:
        errmsg = "Expected socket to be set after bind"
        raise AssertionError(errmsg)
    
    listener.close()
    
    if listener.socket is not None:
        errmsg = "Expected socket to be None after close"
        raise AssertionError(errmsg)
    
    if listener.bound_address is not None:
        errmsg = "Expected bound_address to be None after close"
        raise AssertionError(errmsg)
    
    return


def test_close_removes_unix_socket_file():
    """
        Test that close removes Unix socket file.
    """
    _require_unix_sockets()

    with tempfile.TemporaryDirectory() as temp_dir:
        socket_path = os.path.join(temp_dir, "test.sock")
        config = ServerConfig(unix_socket=socket_path)
        listener = SocketListener(config)
        
        listener.bind()
        
        if os.path.exists(socket_path) is not True:
            errmsg = "Expected socket file to exist after bind"
            raise AssertionError(errmsg)
        
        listener.close()
        
        if os.path.exists(socket_path) is True:
            errmsg = "Expected socket file to be removed after close"
            raise AssertionError(errmsg)
    
    return


def test_close_is_idempotent():
    """
        Test that close can be called multiple times safely.
    """
    port = find_available_port()
    config = ServerConfig(host="127.0.0.1", port=port)
    listener = SocketListener(config)
    
    listener.bind()
    listener.close()
    listener.close()  # Should not raise
    
    return


# =============================================================================
# Unit Tests for fileno() Method
# =============================================================================

def test_fileno_returns_descriptor():
    """
        Test that fileno returns the socket file descriptor.
    """
    port = find_available_port()
    config = ServerConfig(host="127.0.0.1", port=port)
    listener = SocketListener(config)
    
    try:
        listener.bind()
        
        fd = listener.fileno()
        
        if fd < 0:
            errmsg = f"Expected positive file descriptor, got {fd}"
            raise AssertionError(errmsg)
    finally:
        listener.close()
    
    return


def test_fileno_raises_when_not_bound():
    """
        Test that fileno raises RuntimeError when socket is not bound.
    """
    config = ServerConfig()
    listener = SocketListener(config)
    
    exception_raised = False
    
    try:
        listener.fileno()
    except RuntimeError as err:
        exception_raised = True
        if "not bound" not in str(err).lower():
            errmsg = f"Expected 'not bound' in error message, got '{err}'"
            raise AssertionError(errmsg)
    
    if exception_raised is not True:
        errmsg = "Expected RuntimeError to be raised"
        raise AssertionError(errmsg)
    
    return


# =============================================================================
# Unit Tests for Context Manager
# =============================================================================

def test_context_manager_closes_socket():
    """
        Test that context manager closes socket on exit.
    """
    port = find_available_port()
    config = ServerConfig(host="127.0.0.1", port=port)
    
    with SocketListener(config) as listener:
        listener.bind()
        
        if listener.socket is None:
            errmsg = "Expected socket to be set after bind"
            raise AssertionError(errmsg)
    
    if listener.socket is not None:
        errmsg = "Expected socket to be None after context exit"
        raise AssertionError(errmsg)
    
    return


# =============================================================================
# Unit Tests for Error Handling
# =============================================================================

def test_bind_raises_for_invalid_address():
    """
        Test that bind raises BindError for invalid address.
    """
    config = ServerConfig(host="invalid.host.that.does.not.exist.example", port=8000)
    listener = SocketListener(config)
    
    exception_raised = False
    
    try:
        listener.bind()
    except BindError as err:
        exception_raised = True
        if "invalid.host.that.does.not.exist.example" not in err.address:
            errmsg = f"Expected address in error, got '{err.address}'"
            raise AssertionError(errmsg)
    
    if exception_raised is not True:
        errmsg = "Expected BindError to be raised"
        raise AssertionError(errmsg)
    
    return


def test_bind_raises_for_port_in_use():
    """
        Test that bind raises BindError when port is already in use.
        
        Note: This test creates a listening socket that holds the port
        without SO_REUSEPORT so the port is truly in use and cannot be
        shared. On Windows SO_REUSEADDR lets a second socket bind an
        address that is already in LISTEN state, so the holder is bound
        with SO_EXCLUSIVEADDRUSE there, which makes the second bind fail
        with WSAEADDRINUSE just as it fails with EADDRINUSE on POSIX.
    """
    port = find_available_port()
    
    # Create a socket that holds the port without SO_REUSEPORT
    blocking_socket = socket_module.socket(socket_module.AF_INET, socket_module.SOCK_STREAM)
    if hasattr(socket_module, "SO_EXCLUSIVEADDRUSE"):
        blocking_socket.setsockopt(socket_module.SOL_SOCKET, socket_module.SO_EXCLUSIVEADDRUSE, 1)
    else:
        blocking_socket.setsockopt(socket_module.SOL_SOCKET, socket_module.SO_REUSEADDR, 1)
    # Explicitly disable SO_REUSEPORT if available
    if hasattr(socket_module, "SO_REUSEPORT"):
        try:
            blocking_socket.setsockopt(socket_module.SOL_SOCKET, socket_module.SO_REUSEPORT, 0)
        except OSError:
            # Best-effort: SO_REUSEPORT is off by default, so a platform that rejects
            # explicitly clearing it still leaves the holder socket exclusive.
            pass
    
    try:
        blocking_socket.bind(("127.0.0.1", port))
        blocking_socket.listen(1)
        
        # Now try to bind with SocketListener - should fail
        config = ServerConfig(host="127.0.0.1", port=port)
        listener = SocketListener(config)
        
        exception_raised = False
        
        try:
            listener.bind()
            # If bind succeeded, close it
            listener.close()
        except BindError:
            exception_raised = True
        except OSError:
            # OSError is also acceptable for port in use
            exception_raised = True
        
        if exception_raised is not True:
            errmsg = "Expected BindError or OSError to be raised for port in use"
            raise AssertionError(errmsg)
    finally:
        blocking_socket.close()
    
    return


# =============================================================================
# Unit Tests for SSL Support
# =============================================================================

def test_ssl_enabled_false_by_default():
    """
        Test that ssl_enabled is False by default.
    """
    config = ServerConfig()
    listener = SocketListener(config)
    
    if listener.ssl_enabled is not False:
        errmsg = "Expected ssl_enabled to be False by default"
        raise AssertionError(errmsg)
    
    return


def test_setup_ssl_without_config_does_nothing():
    """
        Test that setup_ssl does nothing when SSL is not configured.
    """
    port = find_available_port()
    config = ServerConfig(host="127.0.0.1", port=port)
    listener = SocketListener(config)
    
    try:
        listener.bind()
        listener.setup_ssl()  # Should not raise
        
        if listener.ssl_enabled is not False:
            errmsg = "Expected ssl_enabled to remain False"
            raise AssertionError(errmsg)
    finally:
        listener.close()
    
    return
