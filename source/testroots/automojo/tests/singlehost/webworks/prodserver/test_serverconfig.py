"""
    Tests for the production server ServerConfig dataclass.

    This module contains unit tests for the production server configuration
    functionality including default values, validation, auto-detection of
    worker count, ServerState enum, and exit code constants.
"""

import os

from automojo.webworks.prodserver.serverconfig import (
    EXIT_APP_LOAD_ERROR,
    EXIT_BIND_ERROR,
    EXIT_CONFIG_ERROR,
    EXIT_ERROR,
    EXIT_PID_FILE_ERROR,
    EXIT_SUCCESS,
    VALID_LOG_FORMATS,
    VALID_LOG_LEVELS,
    VALID_WORKER_CLASSES,
    ServerConfig,
    ServerState,
)
from automojo.webworks.prodserver.exceptions import ConfigurationError


# =============================================================================
# Unit Tests for ServerConfig Default Values
# =============================================================================

def test_serverconfig_default_host():
    """
        Test that ServerConfig has correct default host.
    """
    config = ServerConfig()

    expected = "0.0.0.0"
    if config.host != expected:
        errmsg = f"Expected default host '{expected}', got '{config.host}'"
        raise AssertionError(errmsg)

    return


def test_serverconfig_default_port():
    """
        Test that ServerConfig has correct default port.
    """
    config = ServerConfig()

    expected = 8000
    if config.port != expected:
        errmsg = f"Expected default port {expected}, got {config.port}"
        raise AssertionError(errmsg)

    return


def test_serverconfig_default_workers():
    """
        Test that ServerConfig has correct default workers (0 for auto-detect).
    """
    config = ServerConfig()

    expected = 0
    if config.workers != expected:
        errmsg = f"Expected default workers {expected}, got {config.workers}"
        raise AssertionError(errmsg)

    return


def test_serverconfig_default_threads():
    """
        Test that ServerConfig has correct default threads.
    """
    config = ServerConfig()

    expected = 1
    if config.threads != expected:
        errmsg = f"Expected default threads {expected}, got {config.threads}"
        raise AssertionError(errmsg)

    return


def test_serverconfig_default_worker_class():
    """
        Test that ServerConfig has correct default worker class.
    """
    config = ServerConfig()

    expected = "sync"
    if config.worker_class != expected:
        errmsg = f"Expected default worker_class '{expected}', got '{config.worker_class}'"
        raise AssertionError(errmsg)

    return


def test_serverconfig_default_timeout():
    """
        Test that ServerConfig has correct default timeout.
    """
    config = ServerConfig()

    expected = 30
    if config.timeout != expected:
        errmsg = f"Expected default timeout {expected}, got {config.timeout}"
        raise AssertionError(errmsg)

    return


def test_serverconfig_default_graceful_timeout():
    """
        Test that ServerConfig has correct default graceful timeout.
    """
    config = ServerConfig()

    expected = 30
    if config.graceful_timeout != expected:
        errmsg = f"Expected default graceful_timeout {expected}, got {config.graceful_timeout}"
        raise AssertionError(errmsg)

    return


def test_serverconfig_default_backlog():
    """
        Test that ServerConfig has correct default backlog.
    """
    config = ServerConfig()

    expected = 2048
    if config.backlog != expected:
        errmsg = f"Expected default backlog {expected}, got {config.backlog}"
        raise AssertionError(errmsg)

    return


def test_serverconfig_default_keep_alive():
    """
        Test that ServerConfig has correct default keep-alive.
    """
    config = ServerConfig()

    expected = 5
    if config.keep_alive != expected:
        errmsg = f"Expected default keep_alive {expected}, got {config.keep_alive}"
        raise AssertionError(errmsg)

    return


def test_serverconfig_default_ssl_fields_none():
    """
        Test that ServerConfig has None for SSL optional fields by default.
    """
    config = ServerConfig()

    if config.ssl_certfile is not None:
        errmsg = f"Expected ssl_certfile None, got '{config.ssl_certfile}'"
        raise AssertionError(errmsg)

    if config.ssl_keyfile is not None:
        errmsg = f"Expected ssl_keyfile None, got '{config.ssl_keyfile}'"
        raise AssertionError(errmsg)

    if config.ssl_ca_certs is not None:
        errmsg = f"Expected ssl_ca_certs None, got '{config.ssl_ca_certs}'"
        raise AssertionError(errmsg)

    return


def test_serverconfig_default_ssl_ciphers():
    """
        Test that ServerConfig has correct default SSL ciphers.
    """
    config = ServerConfig()

    expected = "TLS_AES_256_GCM_SHA384:TLS_CHACHA20_POLY1305_SHA256"
    if config.ssl_ciphers != expected:
        errmsg = f"Expected default ssl_ciphers '{expected}', got '{config.ssl_ciphers}'"
        raise AssertionError(errmsg)

    return


def test_serverconfig_default_log_level():
    """
        Test that ServerConfig has correct default log level.
    """
    config = ServerConfig()

    expected = "INFO"
    if config.log_level != expected:
        errmsg = f"Expected default log_level '{expected}', got '{config.log_level}'"
        raise AssertionError(errmsg)

    return


def test_serverconfig_default_log_format():
    """
        Test that ServerConfig has correct default log format.
    """
    config = ServerConfig()

    expected = "standard"
    if config.log_format != expected:
        errmsg = f"Expected default log_format '{expected}', got '{config.log_format}'"
        raise AssertionError(errmsg)

    return


def test_serverconfig_default_health_check_path():
    """
        Test that ServerConfig has correct default health check path.
    """
    config = ServerConfig()

    expected = "/health"
    if config.health_check_path != expected:
        errmsg = f"Expected default health_check_path '{expected}', got '{config.health_check_path}'"
        raise AssertionError(errmsg)

    return


def test_serverconfig_default_metrics_path():
    """
        Test that ServerConfig has correct default metrics path.
    """
    config = ServerConfig()

    expected = "/metrics"
    if config.metrics_path != expected:
        errmsg = f"Expected default metrics_path '{expected}', got '{config.metrics_path}'"
        raise AssertionError(errmsg)

    return


def test_serverconfig_default_trace_header():
    """
        Test that ServerConfig has correct default trace header.
    """
    config = ServerConfig()

    expected = "X-Request-ID"
    if config.trace_header != expected:
        errmsg = f"Expected default trace_header '{expected}', got '{config.trace_header}'"
        raise AssertionError(errmsg)

    return


def test_serverconfig_default_hooks_none():
    """
        Test that ServerConfig has None for all hook fields by default.
    """
    config = ServerConfig()

    if config.on_starting is not None:
        errmsg = f"Expected on_starting None, got '{config.on_starting}'"
        raise AssertionError(errmsg)

    if config.on_reload is not None:
        errmsg = f"Expected on_reload None, got '{config.on_reload}'"
        raise AssertionError(errmsg)

    if config.when_ready is not None:
        errmsg = f"Expected when_ready None, got '{config.when_ready}'"
        raise AssertionError(errmsg)

    if config.on_exit is not None:
        errmsg = f"Expected on_exit None, got '{config.on_exit}'"
        raise AssertionError(errmsg)

    return


def test_serverconfig_custom_values():
    """
        Test that ServerConfig accepts custom values.
    """
    config = ServerConfig(
        host="127.0.0.1",
        port=9000,
        workers=4,
        threads=2,
        worker_class="async",
        timeout=60,
        log_level="DEBUG",
        enable_tracing=True
    )

    if config.host != "127.0.0.1":
        errmsg = f"Expected host '127.0.0.1', got '{config.host}'"
        raise AssertionError(errmsg)

    if config.port != 9000:
        errmsg = f"Expected port 9000, got {config.port}"
        raise AssertionError(errmsg)

    if config.workers != 4:
        errmsg = f"Expected workers 4, got {config.workers}"
        raise AssertionError(errmsg)

    if config.threads != 2:
        errmsg = f"Expected threads 2, got {config.threads}"
        raise AssertionError(errmsg)

    if config.worker_class != "async":
        errmsg = f"Expected worker_class 'async', got '{config.worker_class}'"
        raise AssertionError(errmsg)

    if config.timeout != 60:
        errmsg = f"Expected timeout 60, got {config.timeout}"
        raise AssertionError(errmsg)

    if config.log_level != "DEBUG":
        errmsg = f"Expected log_level 'DEBUG', got '{config.log_level}'"
        raise AssertionError(errmsg)

    if config.enable_tracing is not True:
        errmsg = f"Expected enable_tracing True, got {config.enable_tracing}"
        raise AssertionError(errmsg)

    return


# =============================================================================
# Unit Tests for resolve_workers()
# =============================================================================

def test_resolve_workers_auto_detect():
    """
        Test that resolve_workers auto-detects based on CPU cores when workers is 0.
    """
    config = ServerConfig(workers=0)

    result = config.resolve_workers()

    cpu_count = os.cpu_count()
    if cpu_count is None:
        cpu_count = 1
    expected = cpu_count * 2 + 1

    if result != expected:
        errmsg = f"Expected resolve_workers to return {expected}, got {result}"
        raise AssertionError(errmsg)

    return


def test_resolve_workers_explicit_count():
    """
        Test that resolve_workers returns the explicit count when workers is non-zero.
    """
    config = ServerConfig(workers=8)

    result = config.resolve_workers()

    expected = 8
    if result != expected:
        errmsg = f"Expected resolve_workers to return {expected}, got {result}"
        raise AssertionError(errmsg)

    return


def test_resolve_workers_returns_positive():
    """
        Test that resolve_workers always returns a positive integer.
    """
    config = ServerConfig(workers=0)

    result = config.resolve_workers()

    if result < 1:
        errmsg = f"Expected resolve_workers to return at least 1, got {result}"
        raise AssertionError(errmsg)

    return


# =============================================================================
# Unit Tests for validate()
# =============================================================================

def test_validate_passes_for_valid_config():
    """
        Test that validate passes for valid default configuration.
    """
    config = ServerConfig()

    # Should not raise
    config.validate()

    return


def test_validate_passes_for_valid_custom_config():
    """
        Test that validate passes for valid custom configuration.
    """
    config = ServerConfig(
        host="127.0.0.1",
        port=443,
        workers=4,
        threads=2,
        worker_class="async",
        timeout=60,
        log_level="DEBUG",
        log_format="json"
    )

    # Should not raise
    config.validate()

    return


def test_validate_raises_for_port_too_high():
    """
        Test that validate raises for port above 65535.
    """
    config = ServerConfig(port=70000)

    exception_raised = False

    try:
        config.validate()
    except ConfigurationError as err:
        exception_raised = True
        if "port" not in str(err).lower():
            errmsg = f"Expected 'port' in error message, got '{err}'"
            raise AssertionError(errmsg)

    if exception_raised is not True:
        errmsg = "Expected ConfigurationError to be raised for port 70000"
        raise AssertionError(errmsg)

    return


def test_validate_raises_for_negative_port():
    """
        Test that validate raises for negative port.
    """
    config = ServerConfig(port=-1)

    exception_raised = False

    try:
        config.validate()
    except ConfigurationError as err:
        exception_raised = True

    if exception_raised is not True:
        errmsg = "Expected ConfigurationError to be raised for port -1"
        raise AssertionError(errmsg)

    return


def test_validate_raises_for_negative_workers():
    """
        Test that validate raises for negative workers.
    """
    config = ServerConfig(workers=-1)

    exception_raised = False

    try:
        config.validate()
    except ConfigurationError as err:
        exception_raised = True
        if "workers" not in str(err).lower():
            errmsg = f"Expected 'workers' in error message, got '{err}'"
            raise AssertionError(errmsg)

    if exception_raised is not True:
        errmsg = "Expected ConfigurationError to be raised for workers -1"
        raise AssertionError(errmsg)

    return


def test_validate_allows_zero_workers():
    """
        Test that validate allows workers=0 for auto-detect.
    """
    config = ServerConfig(workers=0)

    # Should not raise
    config.validate()

    return


def test_validate_raises_for_zero_threads():
    """
        Test that validate raises for zero threads.
    """
    config = ServerConfig(threads=0)

    exception_raised = False

    try:
        config.validate()
    except ConfigurationError as err:
        exception_raised = True
        if "threads" not in str(err).lower():
            errmsg = f"Expected 'threads' in error message, got '{err}'"
            raise AssertionError(errmsg)

    if exception_raised is not True:
        errmsg = "Expected ConfigurationError to be raised for threads 0"
        raise AssertionError(errmsg)

    return


def test_validate_raises_for_invalid_worker_class():
    """
        Test that validate raises for invalid worker class.
    """
    config = ServerConfig(worker_class="invalid")

    exception_raised = False

    try:
        config.validate()
    except ConfigurationError as err:
        exception_raised = True
        if "worker class" not in str(err).lower():
            errmsg = f"Expected 'worker class' in error message, got '{err}'"
            raise AssertionError(errmsg)

    if exception_raised is not True:
        errmsg = "Expected ConfigurationError to be raised for worker_class 'invalid'"
        raise AssertionError(errmsg)

    return


def test_validate_raises_for_negative_timeout():
    """
        Test that validate raises for negative timeout.
    """
    config = ServerConfig(timeout=-1)

    exception_raised = False

    try:
        config.validate()
    except ConfigurationError as err:
        exception_raised = True
        if "timeout" not in str(err).lower():
            errmsg = f"Expected 'timeout' in error message, got '{err}'"
            raise AssertionError(errmsg)

    if exception_raised is not True:
        errmsg = "Expected ConfigurationError to be raised for timeout -1"
        raise AssertionError(errmsg)

    return


def test_validate_raises_for_negative_graceful_timeout():
    """
        Test that validate raises for negative graceful timeout.
    """
    config = ServerConfig(graceful_timeout=-5)

    exception_raised = False

    try:
        config.validate()
    except ConfigurationError as err:
        exception_raised = True
        if "graceful timeout" not in str(err).lower():
            errmsg = f"Expected 'graceful timeout' in error message, got '{err}'"
            raise AssertionError(errmsg)

    if exception_raised is not True:
        errmsg = "Expected ConfigurationError to be raised for graceful_timeout -5"
        raise AssertionError(errmsg)

    return


def test_validate_raises_for_invalid_log_level():
    """
        Test that validate raises for invalid log level.
    """
    config = ServerConfig(log_level="INVALID")

    exception_raised = False

    try:
        config.validate()
    except ConfigurationError as err:
        exception_raised = True
        if "log level" not in str(err).lower():
            errmsg = f"Expected 'log level' in error message, got '{err}'"
            raise AssertionError(errmsg)

    if exception_raised is not True:
        errmsg = "Expected ConfigurationError to be raised for log_level 'INVALID'"
        raise AssertionError(errmsg)

    return


def test_validate_raises_for_invalid_log_format():
    """
        Test that validate raises for invalid log format.
    """
    config = ServerConfig(log_format="xml")

    exception_raised = False

    try:
        config.validate()
    except ConfigurationError as err:
        exception_raised = True
        if "log format" not in str(err).lower():
            errmsg = f"Expected 'log format' in error message, got '{err}'"
            raise AssertionError(errmsg)

    if exception_raised is not True:
        errmsg = "Expected ConfigurationError to be raised for log_format 'xml'"
        raise AssertionError(errmsg)

    return


def test_validate_raises_for_ssl_cert_without_key():
    """
        Test that validate raises when SSL cert is provided without key.
    """
    config = ServerConfig(ssl_certfile="/path/to/cert.pem", ssl_keyfile=None)

    exception_raised = False

    try:
        config.validate()
    except ConfigurationError as err:
        exception_raised = True
        if "ssl" not in str(err).lower():
            errmsg = f"Expected 'ssl' in error message, got '{err}'"
            raise AssertionError(errmsg)

    if exception_raised is not True:
        errmsg = "Expected ConfigurationError to be raised for ssl_certfile without ssl_keyfile"
        raise AssertionError(errmsg)

    return


def test_validate_raises_for_ssl_key_without_cert():
    """
        Test that validate raises when SSL key is provided without cert.
    """
    config = ServerConfig(ssl_certfile=None, ssl_keyfile="/path/to/key.pem")

    exception_raised = False

    try:
        config.validate()
    except ConfigurationError as err:
        exception_raised = True
        if "ssl" not in str(err).lower():
            errmsg = f"Expected 'ssl' in error message, got '{err}'"
            raise AssertionError(errmsg)

    if exception_raised is not True:
        errmsg = "Expected ConfigurationError to be raised for ssl_keyfile without ssl_certfile"
        raise AssertionError(errmsg)

    return


def test_validate_collects_multiple_errors():
    """
        Test that validate collects multiple validation errors.
    """
    config = ServerConfig(
        port=-1,
        workers=-1,
        threads=0,
        timeout=-1
    )

    exception_raised = False

    try:
        config.validate()
    except ConfigurationError as err:
        exception_raised = True
        if len(err.errors) < 4:
            errmsg = f"Expected at least 4 errors, got {len(err.errors)}: {err.errors}"
            raise AssertionError(errmsg)

    if exception_raised is not True:
        errmsg = "Expected ConfigurationError to be raised"
        raise AssertionError(errmsg)

    return


def test_validate_raises_for_negative_limit_request_line():
    """
        Test that validate raises for negative limit_request_line.
    """
    config = ServerConfig(limit_request_line=-1)

    exception_raised = False

    try:
        config.validate()
    except ConfigurationError as err:
        exception_raised = True

    if exception_raised is not True:
        errmsg = "Expected ConfigurationError to be raised for limit_request_line -1"
        raise AssertionError(errmsg)

    return


def test_validate_raises_for_zero_backlog():
    """
        Test that validate raises for zero backlog.
    """
    config = ServerConfig(backlog=0)

    exception_raised = False

    try:
        config.validate()
    except ConfigurationError as err:
        exception_raised = True
        if "backlog" not in str(err).lower():
            errmsg = f"Expected 'backlog' in error message, got '{err}'"
            raise AssertionError(errmsg)

    if exception_raised is not True:
        errmsg = "Expected ConfigurationError to be raised for backlog 0"
        raise AssertionError(errmsg)

    return


# =============================================================================
# Unit Tests for as_dict()
# =============================================================================

def test_as_dict_returns_all_fields():
    """
        Test that as_dict returns all serializable configuration fields.
    """
    config = ServerConfig(host="127.0.0.1", port=9000)

    result = config.as_dict()

    expected_fields = [
        "host", "port", "workers", "threads", "worker_class",
        "max_requests", "max_requests_jitter", "timeout", "graceful_timeout",
        "backlog", "keep_alive", "max_connections",
        "limit_request_line", "limit_request_fields",
        "limit_request_field_size", "limit_request_body", "limit_memory",
        "ssl_certfile", "ssl_keyfile", "ssl_ca_certs",
        "ssl_ciphers", "ssl_version", "ssl_redirect",
        "pid_file", "daemon", "user", "group", "umask", "chdir", "preload",
        "log_format", "access_log", "error_log", "log_level",
        "health_check_path", "metrics_path", "statsd_host", "statsd_port",
        "trace_header", "enable_tracing",
    ]

    for field_name in expected_fields:
        if field_name not in result:
            errmsg = f"Expected field '{field_name}' in as_dict result"
            raise AssertionError(errmsg)

    if result["host"] != "127.0.0.1":
        errmsg = f"Expected host '127.0.0.1', got '{result['host']}'"
        raise AssertionError(errmsg)

    if result["port"] != 9000:
        errmsg = f"Expected port 9000, got {result['port']}"
        raise AssertionError(errmsg)

    return


def test_as_dict_excludes_hooks():
    """
        Test that as_dict excludes callable hook fields.
    """
    def dummy_hook():
        """
            A dummy hook for testing.
        """
        return

    config = ServerConfig(on_starting=dummy_hook)

    result = config.as_dict()

    if "on_starting" in result:
        errmsg = "Expected 'on_starting' to be excluded from as_dict result"
        raise AssertionError(errmsg)

    if "on_reload" in result:
        errmsg = "Expected 'on_reload' to be excluded from as_dict result"
        raise AssertionError(errmsg)

    if "when_ready" in result:
        errmsg = "Expected 'when_ready' to be excluded from as_dict result"
        raise AssertionError(errmsg)

    if "on_exit" in result:
        errmsg = "Expected 'on_exit' to be excluded from as_dict result"
        raise AssertionError(errmsg)

    return


# =============================================================================
# Unit Tests for ServerState Enum
# =============================================================================

def test_serverstate_stopped():
    """
        Test that ServerState.STOPPED has correct value.
    """
    if ServerState.STOPPED.value != "stopped":
        errmsg = f"Expected ServerState.STOPPED value 'stopped', got '{ServerState.STOPPED.value}'"
        raise AssertionError(errmsg)

    return


def test_serverstate_starting():
    """
        Test that ServerState.STARTING has correct value.
    """
    if ServerState.STARTING.value != "starting":
        errmsg = f"Expected ServerState.STARTING value 'starting', got '{ServerState.STARTING.value}'"
        raise AssertionError(errmsg)

    return


def test_serverstate_running():
    """
        Test that ServerState.RUNNING has correct value.
    """
    if ServerState.RUNNING.value != "running":
        errmsg = f"Expected ServerState.RUNNING value 'running', got '{ServerState.RUNNING.value}'"
        raise AssertionError(errmsg)

    return


def test_serverstate_shutting_down():
    """
        Test that ServerState.SHUTTING_DOWN has correct value.
    """
    if ServerState.SHUTTING_DOWN.value != "shutting_down":
        errmsg = f"Expected ServerState.SHUTTING_DOWN value 'shutting_down', got '{ServerState.SHUTTING_DOWN.value}'"
        raise AssertionError(errmsg)

    return


def test_serverstate_reloading():
    """
        Test that ServerState.RELOADING has correct value.
    """
    if ServerState.RELOADING.value != "reloading":
        errmsg = f"Expected ServerState.RELOADING value 'reloading', got '{ServerState.RELOADING.value}'"
        raise AssertionError(errmsg)

    return


def test_serverstate_has_five_members():
    """
        Test that ServerState has exactly five members.
    """
    member_count = len(ServerState)

    if member_count != 5:
        errmsg = f"Expected ServerState to have 5 members, got {member_count}"
        raise AssertionError(errmsg)

    return


# =============================================================================
# Unit Tests for Exit Codes
# =============================================================================

def test_exit_codes_values():
    """
        Test that exit code constants have correct values.
    """
    if EXIT_SUCCESS != 0:
        errmsg = f"Expected EXIT_SUCCESS=0, got {EXIT_SUCCESS}"
        raise AssertionError(errmsg)

    if EXIT_ERROR != 1:
        errmsg = f"Expected EXIT_ERROR=1, got {EXIT_ERROR}"
        raise AssertionError(errmsg)

    if EXIT_CONFIG_ERROR != 2:
        errmsg = f"Expected EXIT_CONFIG_ERROR=2, got {EXIT_CONFIG_ERROR}"
        raise AssertionError(errmsg)

    if EXIT_BIND_ERROR != 3:
        errmsg = f"Expected EXIT_BIND_ERROR=3, got {EXIT_BIND_ERROR}"
        raise AssertionError(errmsg)

    if EXIT_APP_LOAD_ERROR != 4:
        errmsg = f"Expected EXIT_APP_LOAD_ERROR=4, got {EXIT_APP_LOAD_ERROR}"
        raise AssertionError(errmsg)

    if EXIT_PID_FILE_ERROR != 5:
        errmsg = f"Expected EXIT_PID_FILE_ERROR=5, got {EXIT_PID_FILE_ERROR}"
        raise AssertionError(errmsg)

    return


# =============================================================================
# Unit Tests for ConfigurationError
# =============================================================================

def test_configuration_error_stores_errors():
    """
        Test that ConfigurationError stores the list of errors.
    """
    errors = ["Error one", "Error two"]
    err = ConfigurationError(errors)

    if len(err.errors) != 2:
        errmsg = f"Expected 2 errors, got {len(err.errors)}"
        raise AssertionError(errmsg)

    if err.errors[0] != "Error one":
        errmsg = f"Expected first error 'Error one', got '{err.errors[0]}'"
        raise AssertionError(errmsg)

    if err.errors[1] != "Error two":
        errmsg = f"Expected second error 'Error two', got '{err.errors[1]}'"
        raise AssertionError(errmsg)

    return


def test_configuration_error_message_contains_errors():
    """
        Test that ConfigurationError message contains the error descriptions.
    """
    errors = ["Port is invalid", "Workers is negative"]
    err = ConfigurationError(errors)

    message = str(err)

    if "Port is invalid" not in message:
        errmsg = f"Expected 'Port is invalid' in message, got '{message}'"
        raise AssertionError(errmsg)

    if "Workers is negative" not in message:
        errmsg = f"Expected 'Workers is negative' in message, got '{message}'"
        raise AssertionError(errmsg)

    return


# =============================================================================
# Unit Tests for Valid Constants
# =============================================================================

def test_valid_worker_classes_contains_expected():
    """
        Test that VALID_WORKER_CLASSES contains the expected values.
    """
    expected = {"sync", "async", "gevent"}

    if VALID_WORKER_CLASSES != expected:
        errmsg = f"Expected VALID_WORKER_CLASSES {expected}, got {VALID_WORKER_CLASSES}"
        raise AssertionError(errmsg)

    return


def test_valid_log_levels_contains_expected():
    """
        Test that VALID_LOG_LEVELS contains the expected values.
    """
    expected = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}

    if VALID_LOG_LEVELS != expected:
        errmsg = f"Expected VALID_LOG_LEVELS {expected}, got {VALID_LOG_LEVELS}"
        raise AssertionError(errmsg)

    return


def test_valid_log_formats_contains_expected():
    """
        Test that VALID_LOG_FORMATS contains the expected values.
    """
    expected = {"standard", "json"}

    if VALID_LOG_FORMATS != expected:
        errmsg = f"Expected VALID_LOG_FORMATS {expected}, got {VALID_LOG_FORMATS}"
        raise AssertionError(errmsg)

    return
