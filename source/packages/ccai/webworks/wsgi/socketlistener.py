"""
    Socket listener module for the WSGI layer.
    
    This module provides the SocketListener class for managing server socket
    binding and connection acceptance. It supports IPv4, IPv6, and Unix domain
    sockets with optional SSL/TLS support.
"""

import os
import socket as socket_module
import ssl
from typing import Any, Optional, Tuple

from ccai.webworks.wsgi.exceptions import BindError
from ccai.webworks.wsgi.serverconfig import ServerConfig


class SocketListener:
    """
        Manages server socket binding and connection acceptance.
        
        This class handles the low-level socket operations for the WSGI server
        including binding to IPv4, IPv6, and Unix domain socket addresses,
        configuring socket options, accepting connections, and optional SSL/TLS
        wrapping.
    """
    
    def __init__(self, config: ServerConfig):
        """
            Construct a socket listener.
            
            :param config: Server configuration containing bind address, port,
                          socket options, and SSL settings.
        """
        self._config = config
        self._socket: Optional[socket_module.socket] = None
        self._ssl_context: Optional[ssl.SSLContext] = None
        self._is_unix_socket = False
        self._bound_address: Optional[str] = None
        return
    
    @property
    def config(self) -> ServerConfig:
        """
            Get the server configuration.
            
            :returns: ServerConfig instance.
        """
        return self._config
    
    @property
    def socket(self) -> Optional[socket_module.socket]:
        """
            Get the server socket.
            
            :returns: The server socket or None if not bound.
        """
        return self._socket
    
    @property
    def is_unix_socket(self) -> bool:
        """
            Check if this listener uses a Unix domain socket.
            
            :returns: True if using Unix domain socket, False otherwise.
        """
        return self._is_unix_socket
    
    @property
    def bound_address(self) -> Optional[str]:
        """
            Get the address the socket is bound to.
            
            :returns: Bound address string or None if not bound.
        """
        return self._bound_address
    
    def bind(self) -> None:
        """
            Bind to the configured address.
            
            Supports IPv4, IPv6, and Unix domain sockets. The socket type is
            determined by the configuration:
            - If unix_socket is set, binds to a Unix domain socket
            - Otherwise, binds to host:port using IPv4 or IPv6
            
            :raises: BindError if binding fails.
        """
        if self._config.unix_socket is not None:
            self._bind_unix_socket()
        else:
            self._bind_tcp_socket()
        
        return

    def _bind_unix_socket(self) -> None:
        """
            Bind to a Unix domain socket.
            
            Creates a Unix domain socket and binds to the path specified in
            the configuration. Removes any existing socket file at the path.
            
            :raises: BindError if binding fails or the platform has no
                     Unix domain socket support.
        """
        socket_path = self._config.unix_socket
        
        if not hasattr(socket_module, "AF_UNIX"):
            errmsg = "Unix domain sockets are not supported on this platform"
            raise BindError(socket_path, errmsg)
        
        # Remove existing socket file if present
        if os.path.exists(socket_path):
            try:
                os.unlink(socket_path)
            except OSError as os_err:
                errmsg = f"Failed to remove existing socket file: {os_err}"
                raise BindError(socket_path, errmsg) from os_err
        
        try:
            sock = socket_module.socket(socket_module.AF_UNIX, socket_module.SOCK_STREAM)
            self._configure_socket_options(sock)
            sock.bind(socket_path)
            sock.listen(self._config.backlog)
            
            self._socket = sock
            self._is_unix_socket = True
            self._bound_address = socket_path
        except OSError as os_err:
            errmsg = f"Failed to bind Unix socket: {os_err}"
            raise BindError(socket_path, errmsg) from os_err
        
        return
    
    def _bind_tcp_socket(self) -> None:
        """
            Bind to a TCP socket (IPv4 or IPv6).
            
            Attempts to bind to the configured host and port. First tries to
            resolve the address to determine if it's IPv4 or IPv6, then creates
            the appropriate socket type.
            
            :raises: BindError if binding fails.
        """
        host = self._config.host
        port = self._config.port
        address_str = f"{host}:{port}"
        
        # Determine address family by resolving the host
        addr_info = self._resolve_address(host, port)
        
        if addr_info is None:
            errmsg = f"Could not resolve address {host}"
            raise BindError(address_str, errmsg)
        
        family, socktype, proto, canonname, sockaddr = addr_info
        
        try:
            sock = socket_module.socket(family, socktype, proto)
            self._configure_socket_options(sock)
            
            # For IPv6, enable dual-stack if binding to all interfaces
            if family == socket_module.AF_INET6:
                # Allow IPv4 connections on IPv6 socket if binding to ::
                if host == "::" or host == "::0":
                    try:
                        sock.setsockopt(socket_module.IPPROTO_IPV6, socket_module.IPV6_V6ONLY, 0)
                    except (AttributeError, OSError):
                        # IPV6_V6ONLY may not be available on all platforms
                        pass
            
            sock.bind(sockaddr)
            sock.listen(self._config.backlog)
            
            self._socket = sock
            self._is_unix_socket = False
            self._bound_address = address_str
        except OSError as os_err:
            errmsg = f"Failed to bind TCP socket: {os_err}"
            raise BindError(address_str, errmsg) from os_err
        
        return
    
    def _resolve_address(
        self,
        host: str,
        port: int
    ) -> Optional[Tuple]:
        """
            Resolve a host and port to socket address information.
            
            Attempts to resolve the address, preferring IPv6 if available.
            
            :param host: Host name or IP address.
            :param port: Port number.
            
            :returns: Address info tuple or None if resolution fails.
        """
        try:
            # Get all address info for the host
            addr_infos = socket_module.getaddrinfo(
                host,
                port,
                socket_module.AF_UNSPEC,
                socket_module.SOCK_STREAM,
                0,
                socket_module.AI_PASSIVE
            )
            
            if len(addr_infos) == 0:
                return None
            
            # Prefer IPv6 if available, otherwise use first result
            for info in addr_infos:
                if info[0] == socket_module.AF_INET6:
                    return info
            
            # Fall back to first result (likely IPv4)
            rtnval = addr_infos[0]
            return rtnval
        except socket_module.gaierror:
            return None

    def _configure_socket_options(self, sock: socket_module.socket) -> None:
        """
            Configure socket options.
            
            Sets SO_REUSEADDR and SO_REUSEPORT (if available) on the socket.
            
            :param sock: Socket to configure.
        """
        # Allow address reuse
        sock.setsockopt(socket_module.SOL_SOCKET, socket_module.SO_REUSEADDR, 1)
        
        # Allow port reuse (not available on all platforms)
        if hasattr(socket_module, "SO_REUSEPORT"):
            try:
                sock.setsockopt(socket_module.SOL_SOCKET, socket_module.SO_REUSEPORT, 1)
            except OSError:
                # SO_REUSEPORT may not be supported even if defined
                pass
        
        # Set socket to non-blocking for accept timeout handling
        sock.setblocking(True)
        
        return
    
    def accept(self) -> Tuple[socket_module.socket, Tuple[str, int]]:
        """
            Accept a new connection.
            
            Blocks until a connection is available, then returns the client
            socket and address. If SSL is configured, the client socket is
            wrapped with SSL.
            
            :returns: Tuple of (client_socket, client_address).
                     For Unix sockets, address is ("", 0).
            
            :raises: OSError if accept fails.
            :raises: RuntimeError if socket is not bound.
        """
        if self._socket is None:
            errmsg = "Socket is not bound. Call bind() first."
            raise RuntimeError(errmsg)
        
        client_sock, client_addr = self._socket.accept()
        
        # Normalize address for Unix sockets
        if self._is_unix_socket is True:
            client_addr = ("", 0)
        
        # Wrap with SSL if configured
        if self._ssl_context is not None:
            client_sock = self._wrap_client_ssl(client_sock)
        
        rtnval = (client_sock, client_addr)
        return rtnval
    
    def _wrap_client_ssl(self, client_sock: socket_module.socket) -> ssl.SSLSocket:
        """
            Wrap a client socket with SSL.
            
            :param client_sock: Client socket to wrap.
            
            :returns: SSL-wrapped socket.
        """
        ssl_sock = self._ssl_context.wrap_socket(
            client_sock,
            server_side=True
        )
        return ssl_sock
    
    def setup_ssl(self) -> None:
        """
            Setup SSL context if SSL is configured.
            
            Creates an SSL context with the certificate and key files from
            the configuration. This should be called after bind() if SSL
            is needed.
            
            :raises: BindError if SSL setup fails.
        """
        if self._config.ssl_certfile is None:
            return
        
        try:
            # Create SSL context with secure defaults
            self._ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
            
            # Load certificate and key
            self._ssl_context.load_cert_chain(
                certfile=self._config.ssl_certfile,
                keyfile=self._config.ssl_keyfile
            )
            
            # Load CA certificates if provided
            if self._config.ssl_ca_certs is not None:
                self._ssl_context.load_verify_locations(
                    cafile=self._config.ssl_ca_certs
                )
                self._ssl_context.verify_mode = ssl.CERT_OPTIONAL
        except ssl.SSLError as ssl_err:
            address = self._bound_address or "unknown"
            errmsg = f"Failed to setup SSL: {ssl_err}"
            raise BindError(address, errmsg) from ssl_err
        except FileNotFoundError as file_err:
            address = self._bound_address or "unknown"
            errmsg = f"SSL certificate or key file not found: {file_err}"
            raise BindError(address, errmsg) from file_err
        
        return
    
    @property
    def ssl_enabled(self) -> bool:
        """
            Check if SSL is enabled.
            
            :returns: True if SSL context is configured, False otherwise.
        """
        rtnval = self._ssl_context is not None
        return rtnval
    
    def close(self) -> None:
        """
            Close the server socket.
            
            Closes the socket and cleans up any resources. For Unix domain
            sockets, also removes the socket file.
        """
        if self._socket is not None:
            try:
                self._socket.close()
            except OSError:
                # Ignore errors during close
                pass
            
            self._socket = None
        
        # Remove Unix socket file
        if self._is_unix_socket is True:
            socket_path = self._config.unix_socket
            if socket_path is not None and os.path.exists(socket_path):
                try:
                    os.unlink(socket_path)
                except OSError:
                    # Ignore errors during cleanup
                    pass
        
        self._bound_address = None
        self._ssl_context = None
        
        return
    
    def fileno(self) -> int:
        """
            Return socket file descriptor for select/poll.
            
            :returns: File descriptor number.
            
            :raises: RuntimeError if socket is not bound.
        """
        if self._socket is None:
            errmsg = "Socket is not bound. Call bind() first."
            raise RuntimeError(errmsg)
        
        rtnval = self._socket.fileno()
        return rtnval
    
    def __enter__(self) -> "SocketListener":
        """
            Context manager entry.
            
            :returns: Self.
        """
        return self
    
    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> bool:
        """
            Context manager exit.
            
            Closes the socket on exit.
            
            :returns: False to propagate exceptions.
        """
        self.close()
        return False
