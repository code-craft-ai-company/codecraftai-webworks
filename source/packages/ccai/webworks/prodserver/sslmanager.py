"""
    SSL/TLS manager module for the production server.

    This module provides the SSLManager class that handles SSL context
    creation, cipher suite configuration, TLS version enforcement,
    client certificate verification, and HTTP to HTTPS redirection.
"""

import logging
import ssl
from typing import Any, Dict, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    import socket
    from ccai.webworks.prodserver.serverconfig import ServerConfig


# Default logger for SSL manager
_logger = logging.getLogger("webworks.prodserver.sslmanager")


# Mapping of ssl_version config strings to ssl module protocol constants
_TLS_VERSION_MAP = {
    "TLSv1_2": ssl.TLSVersion.TLSv1_2,
    "TLSv1_3": ssl.TLSVersion.TLSv1_3,
}

# Set of TLS versions considered secure
_SUPPORTED_TLS_VERSIONS = frozenset(_TLS_VERSION_MAP.keys())

# Deprecated protocol strings that must be rejected
_DEPRECATED_TLS_VERSIONS = frozenset({
    "SSLv2",
    "SSLv3",
    "TLSv1",
    "TLSv1_1",
})


class SSLConfigError(Exception):
    """
        Raised when SSL/TLS configuration is invalid.
    """
    pass



class SSLManager:
    """
        Manages SSL/TLS configuration and context for the production server.

        Handles SSL context creation, cipher suite configuration, TLS
        version enforcement, client certificate verification, and HTTP
        to HTTPS redirection decisions.
    """

    def __init__(self, config: "ServerConfig"):
        """
            Construct an SSLManager.

            :param config: Server configuration containing SSL settings.
        """
        self._config = config
        self._ssl_context: Optional[ssl.SSLContext] = None

        return

    @property
    def is_ssl_enabled(self) -> bool:
        """
            Check if SSL is configured.

            SSL is considered enabled when both certfile and keyfile
            are specified in the configuration.

            :returns: True if SSL is enabled.
        """
        rtnval = (
            self._config.ssl_certfile is not None
            and self._config.ssl_keyfile is not None
        )

        return rtnval

    @property
    def ssl_context(self) -> Optional[ssl.SSLContext]:
        """
            Get the current SSL context.

            :returns: The SSL context if created, None otherwise.
        """
        return self._ssl_context

    @property
    def ssl_redirect_enabled(self) -> bool:
        """
            Check if HTTP to HTTPS redirect is enabled.

            :returns: True if ssl_redirect is enabled and SSL is configured.
        """
        rtnval = self._config.ssl_redirect and self.is_ssl_enabled

        return rtnval

    def validate_config(self) -> None:
        """
            Validate SSL configuration.

            Checks that certificate and key files are both specified
            when SSL is partially configured, and that the TLS version
            string is supported.

            :raises: SSLConfigError if configuration is invalid.
        """
        certfile = self._config.ssl_certfile
        keyfile = self._config.ssl_keyfile

        # If neither is set, SSL is simply not enabled
        if certfile is None and keyfile is None:
            return

        # Both must be specified together
        if certfile is not None and keyfile is None:
            raise SSLConfigError(
                "SSL key file is required when certificate file is specified"
            )

        if keyfile is not None and certfile is None:
            raise SSLConfigError(
                "SSL certificate file is required when key file is specified"
            )

        # Validate TLS version
        ssl_version = self._config.ssl_version

        if ssl_version in _DEPRECATED_TLS_VERSIONS:
            raise SSLConfigError(
                f"Deprecated TLS version '{ssl_version}' is not allowed. "
                f"Supported versions: {sorted(_SUPPORTED_TLS_VERSIONS)}"
            )

        if ssl_version not in _SUPPORTED_TLS_VERSIONS:
            raise SSLConfigError(
                f"Unsupported TLS version '{ssl_version}'. "
                f"Supported versions: {sorted(_SUPPORTED_TLS_VERSIONS)}"
            )

        return

    def create_ssl_context(self) -> ssl.SSLContext:
        """
            Create and configure an SSL context.

            Creates an SSLContext with the configured certificate, key,
            cipher suites, TLS version, and optional CA certificates
            for client verification.

            :returns: A configured SSLContext.

            :raises: SSLConfigError if SSL is not enabled or configuration
                     is invalid.
        """
        if not self.is_ssl_enabled:
            raise SSLConfigError(
                "Cannot create SSL context: SSL is not enabled. "
                "Both ssl_certfile and ssl_keyfile must be specified."
            )

        self.validate_config()

        # Create context with TLS_SERVER purpose
        context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)

        # Set minimum TLS version
        min_version = _TLS_VERSION_MAP.get(self._config.ssl_version)
        if min_version is not None:
            context.minimum_version = min_version

        # Disable all deprecated protocols explicitly
        context.options |= ssl.OP_NO_SSLv2
        context.options |= ssl.OP_NO_SSLv3
        context.options |= ssl.OP_NO_TLSv1
        context.options |= ssl.OP_NO_TLSv1_1

        # If minimum is TLS 1.3, also disable TLS 1.2
        if self._config.ssl_version == "TLSv1_3":
            context.minimum_version = ssl.TLSVersion.TLSv1_3

        # Set cipher suites
        self._apply_cipher_config(context)

        # Load certificate and key
        try:
            context.load_cert_chain(
                certfile=self._config.ssl_certfile,
                keyfile=self._config.ssl_keyfile,
            )
        except (ssl.SSLError, OSError) as exc:
            raise SSLConfigError(
                f"Failed to load SSL certificate/key: {exc}"
            ) from exc

        # Load CA certificates for client verification if specified
        if self._config.ssl_ca_certs is not None:
            try:
                context.load_verify_locations(
                    cafile=self._config.ssl_ca_certs
                )
                context.verify_mode = ssl.CERT_REQUIRED
            except (ssl.SSLError, OSError) as exc:
                raise SSLConfigError(
                    f"Failed to load CA certificates: {exc}"
                ) from exc

        self._ssl_context = context

        _logger.info(
            "SSL context created with minimum TLS version %s",
            self._config.ssl_version,
        )

        return context

    def wrap_socket(self, sock: "socket.socket") -> ssl.SSLSocket:
        """
            Wrap a socket with SSL.

            :param sock: The socket to wrap.

            :returns: SSL-wrapped socket.

            :raises: SSLConfigError if SSL context has not been created.
        """
        if self._ssl_context is None:
            raise SSLConfigError(
                "SSL context has not been created. Call create_ssl_context() first."
            )

        rtnval = self._ssl_context.wrap_socket(sock, server_side=True)

        return rtnval

    def should_redirect_http(self, scheme: str) -> bool:
        """
            Check if an HTTP request should be redirected to HTTPS.

            Returns True when SSL redirect is enabled and the request
            scheme is HTTP (not HTTPS).

            :param scheme: The request scheme (e.g. 'http' or 'https').

            :returns: True if the request should be redirected to HTTPS.
        """
        if not self.ssl_redirect_enabled:
            return False

        rtnval = scheme.lower() == "http"

        return rtnval

    def get_redirect_url(self, scheme: str, host: str, path: str) -> str:
        """
            Build the HTTPS redirect URL for an HTTP request.

            :param scheme: The original request scheme.
            :param host: The request host header value.
            :param path: The request path.

            :returns: The HTTPS redirect URL.
        """
        rtnval = f"https://{host}{path}"

        return rtnval

    def get_minimum_tls_version(self) -> str:
        """
            Get the configured minimum TLS version string.

            :returns: The minimum TLS version string (e.g. 'TLSv1_2').
        """
        return self._config.ssl_version

    def is_tls_version_allowed(self, version_string: str) -> bool:
        """
            Check if a TLS version string is allowed by the current
            configuration.

            Deprecated versions (SSLv2, SSLv3, TLSv1, TLSv1_1) are
            always rejected. Additionally, if the minimum version is
            TLSv1_3, then TLSv1_2 is also rejected.

            :param version_string: The TLS version string to check.

            :returns: True if the version is allowed.
        """
        # Always reject deprecated versions
        if version_string in _DEPRECATED_TLS_VERSIONS:
            return False

        # If not a recognized version, reject
        if version_string not in _SUPPORTED_TLS_VERSIONS:
            return False

        # If minimum is TLSv1_3, reject TLSv1_2
        if self._config.ssl_version == "TLSv1_3":
            if version_string == "TLSv1_2":
                return False

        return True

    def get_status(self) -> Dict[str, Any]:
        """
            Get SSL configuration status information.

            :returns: Dictionary with SSL status details.
        """
        rtnval: Dict[str, Any] = {
            "enabled": self.is_ssl_enabled,
            "minimum_tls_version": self._config.ssl_version,
            "ssl_redirect": self._config.ssl_redirect,
            "has_context": self._ssl_context is not None,
            "client_cert_required": self._config.ssl_ca_certs is not None,
        }

        return rtnval

    def _apply_cipher_config(self, context: ssl.SSLContext) -> None:
        """
            Apply cipher suite configuration to the SSL context.

            The ssl module's set_ciphers() only accepts TLS 1.2 cipher
            strings. TLS 1.3 cipher suites are managed automatically by
            the ssl module. This method attempts to set the configured
            ciphers and silently falls back to defaults if the cipher
            string only contains TLS 1.3 suite names.

            :param context: The SSL context to configure.

            :raises: SSLConfigError if the cipher string is truly invalid.
        """
        if not self._config.ssl_ciphers:
            return

        try:
            context.set_ciphers(self._config.ssl_ciphers)
        except ssl.SSLError:
            # TLS 1.3 cipher suite names (e.g. TLS_AES_256_GCM_SHA384)
            # are not accepted by set_ciphers(). If the string looks like
            # it only contains TLS 1.3 suites, fall back to defaults.
            # Otherwise re-raise as a config error.
            parts = [p.strip() for p in self._config.ssl_ciphers.split(":")]
            all_tls13 = all(p.startswith("TLS_") for p in parts if p)

            if not all_tls13:
                raise SSLConfigError(
                    f"Invalid cipher suite configuration: '{self._config.ssl_ciphers}'"
                )

            # TLS 1.3 ciphers are handled automatically by the ssl module
            _logger.debug(
                "Cipher string contains only TLS 1.3 suites, using defaults for TLS 1.2"
            )

        return
