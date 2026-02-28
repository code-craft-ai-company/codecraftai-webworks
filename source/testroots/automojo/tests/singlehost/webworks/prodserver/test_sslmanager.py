"""
    Tests for the production server SSLManager class.

    This module contains unit tests for SSL/TLS management functionality
    including SSL context creation, cipher suite configuration, TLS version
    enforcement, client certificate verification, and HTTP to HTTPS
    redirection.
"""

import os
import ssl
import tempfile

from automojo.webworks.prodserver.serverconfig import ServerConfig
from automojo.webworks.prodserver.sslmanager import (
    SSLConfigError,
    SSLManager,
    _DEPRECATED_TLS_VERSIONS,
    _SUPPORTED_TLS_VERSIONS,
)


# =============================================================================
# Helpers
# =============================================================================

def _create_self_signed_cert(tmpdir: str):
    """
        Create a self-signed certificate and key for testing.

        Uses the ssl module to generate a temporary cert/key pair.

        :returns: Tuple of (certfile_path, keyfile_path).
    """
    # We generate a self-signed cert using openssl via subprocess
    # to avoid needing cryptography as a dependency
    import subprocess

    certfile = os.path.join(tmpdir, "test_cert.pem")
    keyfile = os.path.join(tmpdir, "test_key.pem")

    subprocess.run(
        [
            "openssl", "req", "-x509", "-newkey", "rsa:2048",
            "-keyout", keyfile,
            "-out", certfile,
            "-days", "1",
            "-nodes",
            "-subj", "/CN=localhost",
        ],
        check=True,
        capture_output=True,
    )

    return certfile, keyfile


# =============================================================================
# Unit Tests for SSLManager - Basic Properties
# =============================================================================

def test_ssl_not_enabled_by_default():
    """
        Test that SSL is not enabled with default configuration.
    """
    config = ServerConfig()
    manager = SSLManager(config)

    if manager.is_ssl_enabled:
        errmsg = "Expected SSL to be disabled with default config"
        raise AssertionError(errmsg)

    return


def test_ssl_enabled_when_cert_and_key_specified():
    """
        Test that SSL is enabled when both certfile and keyfile are set.
    """
    config = ServerConfig(
        ssl_certfile="/path/to/cert.pem",
        ssl_keyfile="/path/to/key.pem",
    )
    manager = SSLManager(config)

    if not manager.is_ssl_enabled:
        errmsg = "Expected SSL to be enabled when cert and key are specified"
        raise AssertionError(errmsg)

    return


def test_ssl_context_is_none_before_creation():
    """
        Test that ssl_context is None before create_ssl_context is called.
    """
    config = ServerConfig()
    manager = SSLManager(config)

    if manager.ssl_context is not None:
        errmsg = "Expected ssl_context to be None before creation"
        raise AssertionError(errmsg)

    return



# =============================================================================
# Unit Tests for SSLManager - Validation
# =============================================================================

def test_validate_config_passes_when_ssl_disabled():
    """
        Test that validation passes when SSL is not configured.
    """
    config = ServerConfig()
    manager = SSLManager(config)

    # Should not raise
    manager.validate_config()

    return


def test_validate_config_raises_when_only_certfile():
    """
        Test that validation fails when only certfile is specified.
    """
    config = ServerConfig(ssl_certfile="/path/to/cert.pem")
    manager = SSLManager(config)

    raised = False
    try:
        manager.validate_config()
    except SSLConfigError:
        raised = True

    if not raised:
        errmsg = "Expected SSLConfigError when only certfile is specified"
        raise AssertionError(errmsg)

    return


def test_validate_config_raises_when_only_keyfile():
    """
        Test that validation fails when only keyfile is specified.
    """
    config = ServerConfig(ssl_keyfile="/path/to/key.pem")
    manager = SSLManager(config)

    raised = False
    try:
        manager.validate_config()
    except SSLConfigError:
        raised = True

    if not raised:
        errmsg = "Expected SSLConfigError when only keyfile is specified"
        raise AssertionError(errmsg)

    return


def test_validate_config_raises_for_deprecated_tls_version():
    """
        Test that validation rejects deprecated TLS versions.
    """
    for version in _DEPRECATED_TLS_VERSIONS:
        config = ServerConfig(
            ssl_certfile="/path/to/cert.pem",
            ssl_keyfile="/path/to/key.pem",
            ssl_version=version,
        )
        manager = SSLManager(config)

        raised = False
        try:
            manager.validate_config()
        except SSLConfigError:
            raised = True

        if not raised:
            errmsg = f"Expected SSLConfigError for deprecated version '{version}'"
            raise AssertionError(errmsg)

    return


def test_validate_config_raises_for_unknown_tls_version():
    """
        Test that validation rejects unknown TLS version strings.
    """
    config = ServerConfig(
        ssl_certfile="/path/to/cert.pem",
        ssl_keyfile="/path/to/key.pem",
        ssl_version="TLSv9_9",
    )
    manager = SSLManager(config)

    raised = False
    try:
        manager.validate_config()
    except SSLConfigError:
        raised = True

    if not raised:
        errmsg = "Expected SSLConfigError for unknown TLS version"
        raise AssertionError(errmsg)

    return


def test_validate_config_passes_for_supported_versions():
    """
        Test that validation passes for all supported TLS versions.
    """
    for version in _SUPPORTED_TLS_VERSIONS:
        config = ServerConfig(
            ssl_certfile="/path/to/cert.pem",
            ssl_keyfile="/path/to/key.pem",
            ssl_version=version,
        )
        manager = SSLManager(config)

        # Should not raise
        manager.validate_config()

    return


# =============================================================================
# Unit Tests for SSLManager - Context Creation
# =============================================================================

def test_create_ssl_context_raises_when_ssl_disabled():
    """
        Test that create_ssl_context raises when SSL is not enabled.
    """
    config = ServerConfig()
    manager = SSLManager(config)

    raised = False
    try:
        manager.create_ssl_context()
    except SSLConfigError:
        raised = True

    if not raised:
        errmsg = "Expected SSLConfigError when SSL is not enabled"
        raise AssertionError(errmsg)

    return


def test_create_ssl_context_with_valid_cert():
    """
        Test that create_ssl_context succeeds with valid certificate files.
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        certfile, keyfile = _create_self_signed_cert(tmpdir)

        config = ServerConfig(
            ssl_certfile=certfile,
            ssl_keyfile=keyfile,
            ssl_version="TLSv1_2",
        )
        manager = SSLManager(config)

        context = manager.create_ssl_context()

        if not isinstance(context, ssl.SSLContext):
            errmsg = f"Expected SSLContext, got {type(context).__name__}"
            raise AssertionError(errmsg)

        if manager.ssl_context is None:
            errmsg = "Expected ssl_context to be set after creation"
            raise AssertionError(errmsg)

    return


def test_create_ssl_context_raises_for_invalid_certfile():
    """
        Test that create_ssl_context raises when certificate file is invalid.
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        certfile = os.path.join(tmpdir, "bad_cert.pem")
        keyfile = os.path.join(tmpdir, "bad_key.pem")

        # Write invalid content
        with open(certfile, "w") as f:
            f.write("not a certificate")
        with open(keyfile, "w") as f:
            f.write("not a key")

        config = ServerConfig(
            ssl_certfile=certfile,
            ssl_keyfile=keyfile,
            ssl_version="TLSv1_2",
        )
        manager = SSLManager(config)

        raised = False
        try:
            manager.create_ssl_context()
        except SSLConfigError:
            raised = True

        if not raised:
            errmsg = "Expected SSLConfigError for invalid certificate files"
            raise AssertionError(errmsg)

    return


def test_create_ssl_context_sets_minimum_tls_version():
    """
        Test that the SSL context has the correct minimum TLS version.
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        certfile, keyfile = _create_self_signed_cert(tmpdir)

        config = ServerConfig(
            ssl_certfile=certfile,
            ssl_keyfile=keyfile,
            ssl_version="TLSv1_2",
        )
        manager = SSLManager(config)

        context = manager.create_ssl_context()

        if context.minimum_version != ssl.TLSVersion.TLSv1_2:
            errmsg = (
                f"Expected minimum_version TLSv1_2, "
                f"got {context.minimum_version}"
            )
            raise AssertionError(errmsg)

    return


def test_create_ssl_context_tls13_minimum():
    """
        Test that TLSv1_3 minimum version is set correctly.
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        certfile, keyfile = _create_self_signed_cert(tmpdir)

        config = ServerConfig(
            ssl_certfile=certfile,
            ssl_keyfile=keyfile,
            ssl_version="TLSv1_3",
        )
        manager = SSLManager(config)

        context = manager.create_ssl_context()

        if context.minimum_version != ssl.TLSVersion.TLSv1_3:
            errmsg = (
                f"Expected minimum_version TLSv1_3, "
                f"got {context.minimum_version}"
            )
            raise AssertionError(errmsg)

    return



# =============================================================================
# Unit Tests for SSLManager - Cipher Suite Configuration
# =============================================================================

def test_create_ssl_context_with_custom_ciphers():
    """
        Test that custom cipher suites are applied to the SSL context.
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        certfile, keyfile = _create_self_signed_cert(tmpdir)

        config = ServerConfig(
            ssl_certfile=certfile,
            ssl_keyfile=keyfile,
            ssl_version="TLSv1_2",
            ssl_ciphers="HIGH:!aNULL:!MD5",
        )
        manager = SSLManager(config)

        context = manager.create_ssl_context()

        # Context should be created successfully with custom ciphers
        if not isinstance(context, ssl.SSLContext):
            errmsg = f"Expected SSLContext, got {type(context).__name__}"
            raise AssertionError(errmsg)

    return


def test_create_ssl_context_raises_for_invalid_ciphers():
    """
        Test that invalid cipher suite strings raise SSLConfigError.
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        certfile, keyfile = _create_self_signed_cert(tmpdir)

        config = ServerConfig(
            ssl_certfile=certfile,
            ssl_keyfile=keyfile,
            ssl_version="TLSv1_2",
            ssl_ciphers="COMPLETELY_INVALID_CIPHER_THAT_DOES_NOT_EXIST",
        )
        manager = SSLManager(config)

        raised = False
        try:
            manager.create_ssl_context()
        except SSLConfigError:
            raised = True

        if not raised:
            errmsg = "Expected SSLConfigError for invalid cipher suite"
            raise AssertionError(errmsg)

    return


# =============================================================================
# Unit Tests for SSLManager - TLS Version Enforcement
# =============================================================================

def test_is_tls_version_allowed_rejects_deprecated():
    """
        Test that all deprecated TLS versions are rejected.
    """
    config = ServerConfig(
        ssl_certfile="/path/to/cert.pem",
        ssl_keyfile="/path/to/key.pem",
        ssl_version="TLSv1_2",
    )
    manager = SSLManager(config)

    for version in _DEPRECATED_TLS_VERSIONS:
        if manager.is_tls_version_allowed(version):
            errmsg = f"Expected deprecated version '{version}' to be rejected"
            raise AssertionError(errmsg)

    return


def test_is_tls_version_allowed_accepts_supported():
    """
        Test that supported TLS versions are accepted when minimum is TLSv1_2.
    """
    config = ServerConfig(
        ssl_certfile="/path/to/cert.pem",
        ssl_keyfile="/path/to/key.pem",
        ssl_version="TLSv1_2",
    )
    manager = SSLManager(config)

    for version in _SUPPORTED_TLS_VERSIONS:
        if not manager.is_tls_version_allowed(version):
            errmsg = f"Expected supported version '{version}' to be allowed"
            raise AssertionError(errmsg)

    return


def test_is_tls_version_allowed_tls13_rejects_tls12():
    """
        Test that TLSv1_2 is rejected when minimum is TLSv1_3.
    """
    config = ServerConfig(
        ssl_certfile="/path/to/cert.pem",
        ssl_keyfile="/path/to/key.pem",
        ssl_version="TLSv1_3",
    )
    manager = SSLManager(config)

    if manager.is_tls_version_allowed("TLSv1_2"):
        errmsg = "Expected TLSv1_2 to be rejected when minimum is TLSv1_3"
        raise AssertionError(errmsg)

    if not manager.is_tls_version_allowed("TLSv1_3"):
        errmsg = "Expected TLSv1_3 to be allowed when minimum is TLSv1_3"
        raise AssertionError(errmsg)

    return


def test_is_tls_version_allowed_rejects_unknown():
    """
        Test that unknown TLS version strings are rejected.
    """
    config = ServerConfig(
        ssl_certfile="/path/to/cert.pem",
        ssl_keyfile="/path/to/key.pem",
        ssl_version="TLSv1_2",
    )
    manager = SSLManager(config)

    if manager.is_tls_version_allowed("TLSv9_9"):
        errmsg = "Expected unknown version 'TLSv9_9' to be rejected"
        raise AssertionError(errmsg)

    return


def test_get_minimum_tls_version():
    """
        Test that get_minimum_tls_version returns the configured value.
    """
    config = ServerConfig(
        ssl_certfile="/path/to/cert.pem",
        ssl_keyfile="/path/to/key.pem",
        ssl_version="TLSv1_3",
    )
    manager = SSLManager(config)

    result = manager.get_minimum_tls_version()

    if result != "TLSv1_3":
        errmsg = f"Expected 'TLSv1_3', got '{result}'"
        raise AssertionError(errmsg)

    return


# =============================================================================
# Unit Tests for SSLManager - HTTP to HTTPS Redirect
# =============================================================================

def test_should_redirect_http_when_enabled():
    """
        Test that HTTP requests are redirected when ssl_redirect is enabled.
    """
    config = ServerConfig(
        ssl_certfile="/path/to/cert.pem",
        ssl_keyfile="/path/to/key.pem",
        ssl_redirect=True,
    )
    manager = SSLManager(config)

    if not manager.should_redirect_http("http"):
        errmsg = "Expected redirect for HTTP when ssl_redirect is enabled"
        raise AssertionError(errmsg)

    return


def test_should_not_redirect_https():
    """
        Test that HTTPS requests are not redirected.
    """
    config = ServerConfig(
        ssl_certfile="/path/to/cert.pem",
        ssl_keyfile="/path/to/key.pem",
        ssl_redirect=True,
    )
    manager = SSLManager(config)

    if manager.should_redirect_http("https"):
        errmsg = "Expected no redirect for HTTPS"
        raise AssertionError(errmsg)

    return


def test_should_not_redirect_when_disabled():
    """
        Test that HTTP requests are not redirected when ssl_redirect is off.
    """
    config = ServerConfig(
        ssl_certfile="/path/to/cert.pem",
        ssl_keyfile="/path/to/key.pem",
        ssl_redirect=False,
    )
    manager = SSLManager(config)

    if manager.should_redirect_http("http"):
        errmsg = "Expected no redirect when ssl_redirect is disabled"
        raise AssertionError(errmsg)

    return


def test_should_not_redirect_when_ssl_not_enabled():
    """
        Test that redirect is disabled when SSL is not configured.
    """
    config = ServerConfig(ssl_redirect=True)
    manager = SSLManager(config)

    if manager.should_redirect_http("http"):
        errmsg = "Expected no redirect when SSL is not enabled"
        raise AssertionError(errmsg)

    return


def test_ssl_redirect_enabled_property():
    """
        Test the ssl_redirect_enabled property.
    """
    # Enabled: both SSL and redirect
    config_enabled = ServerConfig(
        ssl_certfile="/path/to/cert.pem",
        ssl_keyfile="/path/to/key.pem",
        ssl_redirect=True,
    )
    manager_enabled = SSLManager(config_enabled)

    if not manager_enabled.ssl_redirect_enabled:
        errmsg = "Expected ssl_redirect_enabled to be True"
        raise AssertionError(errmsg)

    # Disabled: SSL but no redirect
    config_no_redirect = ServerConfig(
        ssl_certfile="/path/to/cert.pem",
        ssl_keyfile="/path/to/key.pem",
        ssl_redirect=False,
    )
    manager_no_redirect = SSLManager(config_no_redirect)

    if manager_no_redirect.ssl_redirect_enabled:
        errmsg = "Expected ssl_redirect_enabled to be False when redirect is off"
        raise AssertionError(errmsg)

    # Disabled: redirect but no SSL
    config_no_ssl = ServerConfig(ssl_redirect=True)
    manager_no_ssl = SSLManager(config_no_ssl)

    if manager_no_ssl.ssl_redirect_enabled:
        errmsg = "Expected ssl_redirect_enabled to be False when SSL is not configured"
        raise AssertionError(errmsg)

    return


def test_get_redirect_url():
    """
        Test that get_redirect_url builds the correct HTTPS URL.
    """
    config = ServerConfig(
        ssl_certfile="/path/to/cert.pem",
        ssl_keyfile="/path/to/key.pem",
        ssl_redirect=True,
    )
    manager = SSLManager(config)

    url = manager.get_redirect_url("http", "example.com", "/api/data")

    expected = "https://example.com/api/data"
    if url != expected:
        errmsg = f"Expected '{expected}', got '{url}'"
        raise AssertionError(errmsg)

    return


# =============================================================================
# Unit Tests for SSLManager - Wrap Socket
# =============================================================================

def test_wrap_socket_raises_without_context():
    """
        Test that wrap_socket raises when SSL context has not been created.
    """
    config = ServerConfig(
        ssl_certfile="/path/to/cert.pem",
        ssl_keyfile="/path/to/key.pem",
    )
    manager = SSLManager(config)

    raised = False
    try:
        manager.wrap_socket(None)
    except SSLConfigError:
        raised = True

    if not raised:
        errmsg = "Expected SSLConfigError when context not created"
        raise AssertionError(errmsg)

    return


# =============================================================================
# Unit Tests for SSLManager - Status
# =============================================================================

def test_get_status_ssl_disabled():
    """
        Test get_status when SSL is not configured.
    """
    config = ServerConfig()
    manager = SSLManager(config)

    status = manager.get_status()

    if status["enabled"] is not False:
        errmsg = f"Expected enabled=False, got {status['enabled']}"
        raise AssertionError(errmsg)

    if status["has_context"] is not False:
        errmsg = f"Expected has_context=False, got {status['has_context']}"
        raise AssertionError(errmsg)

    return


def test_get_status_ssl_enabled():
    """
        Test get_status when SSL is configured.
    """
    config = ServerConfig(
        ssl_certfile="/path/to/cert.pem",
        ssl_keyfile="/path/to/key.pem",
        ssl_version="TLSv1_3",
        ssl_redirect=True,
    )
    manager = SSLManager(config)

    status = manager.get_status()

    if status["enabled"] is not True:
        errmsg = f"Expected enabled=True, got {status['enabled']}"
        raise AssertionError(errmsg)

    if status["minimum_tls_version"] != "TLSv1_3":
        errmsg = f"Expected minimum_tls_version='TLSv1_3', got '{status['minimum_tls_version']}'"
        raise AssertionError(errmsg)

    if status["ssl_redirect"] is not True:
        errmsg = f"Expected ssl_redirect=True, got {status['ssl_redirect']}"
        raise AssertionError(errmsg)

    if status["client_cert_required"] is not False:
        errmsg = f"Expected client_cert_required=False, got {status['client_cert_required']}"
        raise AssertionError(errmsg)

    return


def test_get_status_with_ca_certs():
    """
        Test get_status shows client cert required when ca_certs is set.
    """
    config = ServerConfig(
        ssl_certfile="/path/to/cert.pem",
        ssl_keyfile="/path/to/key.pem",
        ssl_ca_certs="/path/to/ca.pem",
    )
    manager = SSLManager(config)

    status = manager.get_status()

    if status["client_cert_required"] is not True:
        errmsg = f"Expected client_cert_required=True, got {status['client_cert_required']}"
        raise AssertionError(errmsg)

    return
