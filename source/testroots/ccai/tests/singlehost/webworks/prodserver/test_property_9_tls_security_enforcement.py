"""
    Property-Based Tests for TLS Security Enforcement (Property 9).

    Property 9: TLS Security Enforcement
    For any connection attempt using deprecated TLS versions (SSLv2, SSLv3,
    TLS 1.0, TLS 1.1), the server SHALL reject the connection when SSL is
    configured with minimum version TLS 1.2 or higher.

    Validates: Requirements 10.5, 10.6
"""

import random

from ccai.webworks.prodserver.serverconfig import ServerConfig
from ccai.webworks.prodserver.sslmanager import (
    SSLConfigError,
    SSLManager,
    _DEPRECATED_TLS_VERSIONS,
    _SUPPORTED_TLS_VERSIONS,
)


# =============================================================================
# Helpers
# =============================================================================

DEPRECATED_VERSIONS = list(_DEPRECATED_TLS_VERSIONS)
SUPPORTED_VERSIONS = list(_SUPPORTED_TLS_VERSIONS)

# All possible minimum TLS version configurations
MINIMUM_VERSIONS = ["TLSv1_2", "TLSv1_3"]

# Cipher suite options for randomization
CIPHER_SUITES = [
    "TLS_AES_256_GCM_SHA384:TLS_CHACHA20_POLY1305_SHA256",
    "HIGH:!aNULL:!MD5",
    "DEFAULT",
]


# =============================================================================
# Random Generators
# =============================================================================

def generate_deprecated_version() -> str:
    """
        Generate a random deprecated TLS version string.
    """
    return random.choice(DEPRECATED_VERSIONS)


def generate_supported_version() -> str:
    """
        Generate a random supported TLS version string.
    """
    return random.choice(SUPPORTED_VERSIONS)


def generate_minimum_version() -> str:
    """
        Generate a random minimum TLS version configuration.
    """
    return random.choice(MINIMUM_VERSIONS)


def generate_cipher_suite() -> str:
    """
        Generate a random cipher suite string.
    """
    return random.choice(CIPHER_SUITES)


def generate_ssl_config(min_version: str = None) -> ServerConfig:
    """
        Generate a ServerConfig with SSL enabled and a random or
        specified minimum TLS version.
    """
    if min_version is None:
        min_version = generate_minimum_version()

    config = ServerConfig(
        ssl_certfile="/path/to/cert.pem",
        ssl_keyfile="/path/to/key.pem",
        ssl_version=min_version,
        ssl_ciphers=generate_cipher_suite(),
    )

    return config



# =============================================================================
# Property-Based Tests
# =============================================================================

# Feature: production-server, Property 9: TLS Security Enforcement
# *For any* connection attempt using deprecated TLS versions (SSLv2, SSLv3,
# TLS 1.0, TLS 1.1), the server SHALL reject the connection when SSL is
# configured with minimum version TLS 1.2 or higher.
# **Validates: Requirements 10.5, 10.6**


def test_property_9_deprecated_versions_always_rejected():
    """
        Property 9: Deprecated Versions Always Rejected

        For any deprecated TLS version and any minimum TLS version
        configuration, the SSLManager SHALL reject the deprecated version.

        **Validates: Requirement 10.6**
    """
    for iteration in range(100):
        deprecated_version = generate_deprecated_version()
        min_version = generate_minimum_version()

        config = generate_ssl_config(min_version=min_version)
        manager = SSLManager(config)

        if manager.is_tls_version_allowed(deprecated_version):
            errmsg = (
                f"Iteration {iteration}: deprecated version "
                f"'{deprecated_version}' was allowed with minimum "
                f"'{min_version}'"
            )
            raise AssertionError(errmsg)

    return


def test_property_9_deprecated_versions_rejected_in_validation():
    """
        Property 9: Deprecated Versions Rejected in Validation

        For any deprecated TLS version configured as the minimum version,
        the SSLManager SHALL raise SSLConfigError during validation.

        **Validates: Requirement 10.6**
    """
    for iteration in range(100):
        deprecated_version = generate_deprecated_version()

        config = ServerConfig(
            ssl_certfile="/path/to/cert.pem",
            ssl_keyfile="/path/to/key.pem",
            ssl_version=deprecated_version,
        )
        manager = SSLManager(config)

        raised = False
        try:
            manager.validate_config()
        except SSLConfigError:
            raised = True

        if not raised:
            errmsg = (
                f"Iteration {iteration}: expected SSLConfigError for "
                f"deprecated version '{deprecated_version}'"
            )
            raise AssertionError(errmsg)

    return


def test_property_9_supported_versions_accepted_with_tls12_minimum():
    """
        Property 9: Supported Versions Accepted with TLS 1.2 Minimum

        For any supported TLS version, when the minimum is TLSv1_2,
        the SSLManager SHALL accept the version.

        **Validates: Requirement 10.5**
    """
    for iteration in range(100):
        supported_version = generate_supported_version()

        config = generate_ssl_config(min_version="TLSv1_2")
        manager = SSLManager(config)

        if not manager.is_tls_version_allowed(supported_version):
            errmsg = (
                f"Iteration {iteration}: supported version "
                f"'{supported_version}' was rejected with minimum TLSv1_2"
            )
            raise AssertionError(errmsg)

    return


def test_property_9_tls12_rejected_when_minimum_is_tls13():
    """
        Property 9: TLSv1_2 Rejected When Minimum is TLSv1_3

        For any configuration with minimum TLSv1_3, the SSLManager
        SHALL reject TLSv1_2 connections.

        **Validates: Requirement 10.5**
    """
    for iteration in range(100):
        config = generate_ssl_config(min_version="TLSv1_3")
        manager = SSLManager(config)

        if manager.is_tls_version_allowed("TLSv1_2"):
            errmsg = (
                f"Iteration {iteration}: TLSv1_2 was allowed with "
                f"minimum TLSv1_3"
            )
            raise AssertionError(errmsg)

        if not manager.is_tls_version_allowed("TLSv1_3"):
            errmsg = (
                f"Iteration {iteration}: TLSv1_3 was rejected with "
                f"minimum TLSv1_3"
            )
            raise AssertionError(errmsg)

    return


def test_property_9_version_check_consistent_with_validation():
    """
        Property 9: Version Check Consistent with Validation

        For any TLS version string, is_tls_version_allowed and
        validate_config SHALL agree on whether the version is acceptable.
        If a version is deprecated, both SHALL reject it.

        **Validates: Requirements 10.5, 10.6**
    """
    all_versions = DEPRECATED_VERSIONS + SUPPORTED_VERSIONS

    for iteration in range(100):
        version = random.choice(all_versions)
        min_version = generate_minimum_version()

        # Check is_tls_version_allowed
        config_check = generate_ssl_config(min_version=min_version)
        manager_check = SSLManager(config_check)
        allowed = manager_check.is_tls_version_allowed(version)

        # Check validate_config with this version as the configured minimum
        config_validate = ServerConfig(
            ssl_certfile="/path/to/cert.pem",
            ssl_keyfile="/path/to/key.pem",
            ssl_version=version,
        )
        manager_validate = SSLManager(config_validate)

        validation_passed = True
        try:
            manager_validate.validate_config()
        except SSLConfigError:
            validation_passed = False

        # Deprecated versions must be rejected by both
        if version in DEPRECATED_VERSIONS:
            if allowed:
                errmsg = (
                    f"Iteration {iteration}: is_tls_version_allowed "
                    f"accepted deprecated version '{version}'"
                )
                raise AssertionError(errmsg)

            if validation_passed:
                errmsg = (
                    f"Iteration {iteration}: validate_config accepted "
                    f"deprecated version '{version}' as minimum"
                )
                raise AssertionError(errmsg)

    return


def test_property_9_ssl_redirect_requires_ssl_enabled():
    """
        Property 9: SSL Redirect Requires SSL Enabled

        For any configuration, HTTP to HTTPS redirect SHALL only be
        active when both SSL is enabled and ssl_redirect is True.

        **Validates: Requirement 10.8 (related)**
    """
    for iteration in range(100):
        has_cert = random.choice([True, False])
        has_key = random.choice([True, False])
        redirect_flag = random.choice([True, False])

        config = ServerConfig(
            ssl_certfile="/path/to/cert.pem" if has_cert else None,
            ssl_keyfile="/path/to/key.pem" if has_key else None,
            ssl_redirect=redirect_flag,
        )
        manager = SSLManager(config)

        ssl_enabled = has_cert and has_key
        expected_redirect = ssl_enabled and redirect_flag

        if manager.ssl_redirect_enabled != expected_redirect:
            errmsg = (
                f"Iteration {iteration}: ssl_redirect_enabled is "
                f"{manager.ssl_redirect_enabled}, expected {expected_redirect} "
                f"(cert={has_cert}, key={has_key}, redirect={redirect_flag})"
            )
            raise AssertionError(errmsg)

        # Also verify should_redirect_http behavior
        if expected_redirect:
            if not manager.should_redirect_http("http"):
                errmsg = (
                    f"Iteration {iteration}: should_redirect_http('http') "
                    f"returned False when redirect should be active"
                )
                raise AssertionError(errmsg)

            if manager.should_redirect_http("https"):
                errmsg = (
                    f"Iteration {iteration}: should_redirect_http('https') "
                    f"returned True (should never redirect HTTPS)"
                )
                raise AssertionError(errmsg)
        else:
            if manager.should_redirect_http("http"):
                errmsg = (
                    f"Iteration {iteration}: should_redirect_http('http') "
                    f"returned True when redirect should be inactive"
                )
                raise AssertionError(errmsg)

    return
