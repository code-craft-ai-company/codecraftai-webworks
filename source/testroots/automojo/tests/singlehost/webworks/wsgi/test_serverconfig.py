"""
    Tests for the ServerConfig dataclass.
    
    This module contains unit tests for the WSGI server configuration
    functionality including default values, environment loading, file loading,
    and validation.
"""

import json
import os
import tempfile
from typing import Any, Dict

from automojo.webworks.wsgi.serverconfig import ServerConfig, ConfigurationError


# =============================================================================
# Unit Tests for ServerConfig Default Values
# =============================================================================

def test_serverconfig_default_host():
    """
        Test that ServerConfig has correct default host.
    """
    config = ServerConfig()
    
    expected = "127.0.0.1"
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
        Test that ServerConfig has correct default workers.
    """
    config = ServerConfig()
    
    expected = 1
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


def test_serverconfig_default_keepalive():
    """
        Test that ServerConfig has correct default keepalive.
    """
    config = ServerConfig()
    
    expected = 2
    if config.keepalive != expected:
        errmsg = f"Expected default keepalive {expected}, got {config.keepalive}"
        raise AssertionError(errmsg)
    
    return


def test_serverconfig_default_max_header_size():
    """
        Test that ServerConfig has correct default max_header_size.
    """
    config = ServerConfig()
    
    expected = 8192
    if config.max_header_size != expected:
        errmsg = f"Expected default max_header_size {expected}, got {config.max_header_size}"
        raise AssertionError(errmsg)
    
    return


def test_serverconfig_default_max_headers():
    """
        Test that ServerConfig has correct default max_headers.
    """
    config = ServerConfig()
    
    expected = 100
    if config.max_headers != expected:
        errmsg = f"Expected default max_headers {expected}, got {config.max_headers}"
        raise AssertionError(errmsg)
    
    return


def test_serverconfig_default_ssl_fields_none():
    """
        Test that ServerConfig has None for SSL fields by default.
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


def test_serverconfig_default_debug_false():
    """
        Test that ServerConfig has debug False by default.
    """
    config = ServerConfig()
    
    if config.debug is not False:
        errmsg = f"Expected debug False, got {config.debug}"
        raise AssertionError(errmsg)
    
    return


def test_serverconfig_default_reload_false():
    """
        Test that ServerConfig has reload False by default.
    """
    config = ServerConfig()
    
    if config.reload is not False:
        errmsg = f"Expected reload False, got {config.reload}"
        raise AssertionError(errmsg)
    
    return


def test_serverconfig_custom_values():
    """
        Test that ServerConfig accepts custom values.
    """
    config = ServerConfig(
        host="0.0.0.0",
        port=9000,
        workers=4,
        threads=2,
        timeout=60,
        debug=True
    )
    
    if config.host != "0.0.0.0":
        errmsg = f"Expected host '0.0.0.0', got '{config.host}'"
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
    
    if config.timeout != 60:
        errmsg = f"Expected timeout 60, got {config.timeout}"
        raise AssertionError(errmsg)
    
    if config.debug is not True:
        errmsg = f"Expected debug True, got {config.debug}"
        raise AssertionError(errmsg)
    
    return


# =============================================================================
# Unit Tests for from_environ()
# =============================================================================

def test_from_environ_reads_host():
    """
        Test that from_environ reads WSGI_SERVER_HOST.
    """
    original_value = os.environ.get("WSGI_SERVER_HOST")
    
    try:
        os.environ["WSGI_SERVER_HOST"] = "192.168.1.1"
        config = ServerConfig.from_environ()
        
        if config.host != "192.168.1.1":
            errmsg = f"Expected host '192.168.1.1', got '{config.host}'"
            raise AssertionError(errmsg)
    finally:
        if original_value is None:
            os.environ.pop("WSGI_SERVER_HOST", None)
        else:
            os.environ["WSGI_SERVER_HOST"] = original_value
    
    return


def test_from_environ_reads_port():
    """
        Test that from_environ reads WSGI_SERVER_PORT.
    """
    original_value = os.environ.get("WSGI_SERVER_PORT")
    
    try:
        os.environ["WSGI_SERVER_PORT"] = "9000"
        config = ServerConfig.from_environ()
        
        if config.port != 9000:
            errmsg = f"Expected port 9000, got {config.port}"
            raise AssertionError(errmsg)
    finally:
        if original_value is None:
            os.environ.pop("WSGI_SERVER_PORT", None)
        else:
            os.environ["WSGI_SERVER_PORT"] = original_value
    
    return


def test_from_environ_reads_workers():
    """
        Test that from_environ reads WSGI_SERVER_WORKERS.
    """
    original_value = os.environ.get("WSGI_SERVER_WORKERS")
    
    try:
        os.environ["WSGI_SERVER_WORKERS"] = "4"
        config = ServerConfig.from_environ()
        
        if config.workers != 4:
            errmsg = f"Expected workers 4, got {config.workers}"
            raise AssertionError(errmsg)
    finally:
        if original_value is None:
            os.environ.pop("WSGI_SERVER_WORKERS", None)
        else:
            os.environ["WSGI_SERVER_WORKERS"] = original_value
    
    return


def test_from_environ_reads_debug_true():
    """
        Test that from_environ reads WSGI_SERVER_DEBUG as boolean.
    """
    original_value = os.environ.get("WSGI_SERVER_DEBUG")
    
    try:
        os.environ["WSGI_SERVER_DEBUG"] = "true"
        config = ServerConfig.from_environ()
        
        if config.debug is not True:
            errmsg = f"Expected debug True, got {config.debug}"
            raise AssertionError(errmsg)
    finally:
        if original_value is None:
            os.environ.pop("WSGI_SERVER_DEBUG", None)
        else:
            os.environ["WSGI_SERVER_DEBUG"] = original_value
    
    return


def test_from_environ_reads_debug_false():
    """
        Test that from_environ reads WSGI_SERVER_DEBUG as boolean false.
    """
    original_value = os.environ.get("WSGI_SERVER_DEBUG")
    
    try:
        os.environ["WSGI_SERVER_DEBUG"] = "false"
        config = ServerConfig.from_environ()
        
        if config.debug is not False:
            errmsg = f"Expected debug False, got {config.debug}"
            raise AssertionError(errmsg)
    finally:
        if original_value is None:
            os.environ.pop("WSGI_SERVER_DEBUG", None)
        else:
            os.environ["WSGI_SERVER_DEBUG"] = original_value
    
    return


def test_from_environ_uses_defaults_when_not_set():
    """
        Test that from_environ uses defaults when env vars not set.
    """
    # Clear any existing env vars
    env_vars_to_clear = [
        "WSGI_SERVER_HOST", "WSGI_SERVER_PORT", "WSGI_SERVER_WORKERS"
    ]
    original_values = {}
    
    for var in env_vars_to_clear:
        original_values[var] = os.environ.get(var)
        os.environ.pop(var, None)
    
    try:
        config = ServerConfig.from_environ()
        
        if config.host != "127.0.0.1":
            errmsg = f"Expected default host '127.0.0.1', got '{config.host}'"
            raise AssertionError(errmsg)
        
        if config.port != 8000:
            errmsg = f"Expected default port 8000, got {config.port}"
            raise AssertionError(errmsg)
    finally:
        for var, value in original_values.items():
            if value is not None:
                os.environ[var] = value
    
    return


# =============================================================================
# Unit Tests for from_file()
# =============================================================================

def test_from_file_reads_json_config():
    """
        Test that from_file reads JSON configuration file.
    """
    config_data = {
        "host": "0.0.0.0",
        "port": 9000,
        "workers": 4,
        "debug": True
    }
    
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as temp_file:
        json.dump(config_data, temp_file)
        temp_path = temp_file.name
    
    try:
        config = ServerConfig.from_file(temp_path)
        
        if config.host != "0.0.0.0":
            errmsg = f"Expected host '0.0.0.0', got '{config.host}'"
            raise AssertionError(errmsg)
        
        if config.port != 9000:
            errmsg = f"Expected port 9000, got {config.port}"
            raise AssertionError(errmsg)
        
        if config.workers != 4:
            errmsg = f"Expected workers 4, got {config.workers}"
            raise AssertionError(errmsg)
        
        if config.debug is not True:
            errmsg = f"Expected debug True, got {config.debug}"
            raise AssertionError(errmsg)
    finally:
        os.unlink(temp_path)
    
    return


def test_from_file_raises_for_missing_file():
    """
        Test that from_file raises ConfigurationError for missing file.
    """
    exception_raised = False
    
    try:
        ServerConfig.from_file("/nonexistent/path/config.json")
    except ConfigurationError as err:
        exception_raised = True
        if "not found" not in str(err).lower():
            errmsg = f"Expected 'not found' in error message, got '{err}'"
            raise AssertionError(errmsg)
    
    if exception_raised is not True:
        errmsg = "Expected ConfigurationError to be raised"
        raise AssertionError(errmsg)
    
    return


def test_from_file_raises_for_invalid_json():
    """
        Test that from_file raises ConfigurationError for invalid JSON.
    """
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as temp_file:
        temp_file.write("{ invalid json }")
        temp_path = temp_file.name
    
    exception_raised = False
    
    try:
        ServerConfig.from_file(temp_path)
    except ConfigurationError as err:
        exception_raised = True
        if "invalid json" not in str(err).lower():
            errmsg = f"Expected 'invalid json' in error message, got '{err}'"
            raise AssertionError(errmsg)
    finally:
        os.unlink(temp_path)
    
    if exception_raised is not True:
        errmsg = "Expected ConfigurationError to be raised"
        raise AssertionError(errmsg)
    
    return


def test_from_file_ignores_unknown_fields():
    """
        Test that from_file ignores unknown configuration fields.
    """
    config_data = {
        "host": "0.0.0.0",
        "unknown_field": "should be ignored",
        "another_unknown": 12345
    }
    
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as temp_file:
        json.dump(config_data, temp_file)
        temp_path = temp_file.name
    
    try:
        config = ServerConfig.from_file(temp_path)
        
        if config.host != "0.0.0.0":
            errmsg = f"Expected host '0.0.0.0', got '{config.host}'"
            raise AssertionError(errmsg)
        
        # Should not have unknown fields
        if hasattr(config, "unknown_field"):
            errmsg = "Config should not have unknown_field attribute"
            raise AssertionError(errmsg)
    finally:
        os.unlink(temp_path)
    
    return


# =============================================================================
# Unit Tests for validate()
# =============================================================================

def test_validate_passes_for_valid_config():
    """
        Test that validate passes for valid configuration.
    """
    config = ServerConfig()
    
    # Should not raise
    config.validate()
    
    return


def test_validate_raises_for_invalid_port():
    """
        Test that validate raises for invalid port.
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
        errmsg = "Expected ConfigurationError to be raised"
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
        errmsg = "Expected ConfigurationError to be raised"
        raise AssertionError(errmsg)
    
    return


def test_validate_raises_for_zero_workers():
    """
        Test that validate raises for zero workers.
    """
    config = ServerConfig(workers=0)
    
    exception_raised = False
    
    try:
        config.validate()
    except ConfigurationError as err:
        exception_raised = True
        if "workers" not in str(err).lower():
            errmsg = f"Expected 'workers' in error message, got '{err}'"
            raise AssertionError(errmsg)
    
    if exception_raised is not True:
        errmsg = "Expected ConfigurationError to be raised"
        raise AssertionError(errmsg)
    
    return


def test_validate_raises_for_invalid_worker_class():
    """
        Test that validate raises for invalid worker_class.
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
        errmsg = "Expected ConfigurationError to be raised"
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
        errmsg = "Expected ConfigurationError to be raised"
        raise AssertionError(errmsg)
    
    return


def test_validate_raises_for_invalid_log_level():
    """
        Test that validate raises for invalid log_level.
    """
    config = ServerConfig(log_level="invalid")
    
    exception_raised = False
    
    try:
        config.validate()
    except ConfigurationError as err:
        exception_raised = True
        if "log level" not in str(err).lower():
            errmsg = f"Expected 'log level' in error message, got '{err}'"
            raise AssertionError(errmsg)
    
    if exception_raised is not True:
        errmsg = "Expected ConfigurationError to be raised"
        raise AssertionError(errmsg)
    
    return


def test_validate_raises_for_ssl_cert_without_key():
    """
        Test that validate raises when SSL cert is provided without key.
    """
    # Create a temporary file to use as cert
    with tempfile.NamedTemporaryFile(mode="w", suffix=".pem", delete=False) as temp_file:
        temp_file.write("dummy cert")
        cert_path = temp_file.name
    
    try:
        config = ServerConfig(ssl_certfile=cert_path, ssl_keyfile=None)
        
        exception_raised = False
        
        try:
            config.validate()
        except ConfigurationError as err:
            exception_raised = True
            if "ssl" not in str(err).lower():
                errmsg = f"Expected 'ssl' in error message, got '{err}'"
                raise AssertionError(errmsg)
        
        if exception_raised is not True:
            errmsg = "Expected ConfigurationError to be raised"
            raise AssertionError(errmsg)
    finally:
        os.unlink(cert_path)
    
    return


def test_validate_raises_for_missing_ssl_cert_file():
    """
        Test that validate raises when SSL cert file does not exist.
    """
    config = ServerConfig(
        ssl_certfile="/nonexistent/cert.pem",
        ssl_keyfile="/nonexistent/key.pem"
    )
    
    exception_raised = False
    
    try:
        config.validate()
    except ConfigurationError as err:
        exception_raised = True
        if "not found" not in str(err).lower():
            errmsg = f"Expected 'not found' in error message, got '{err}'"
            raise AssertionError(errmsg)
    
    if exception_raised is not True:
        errmsg = "Expected ConfigurationError to be raised"
        raise AssertionError(errmsg)
    
    return


def test_validate_collects_multiple_errors():
    """
        Test that validate collects multiple validation errors.
    """
    config = ServerConfig(
        port=-1,
        workers=0,
        timeout=-1
    )
    
    exception_raised = False
    
    try:
        config.validate()
    except ConfigurationError as err:
        exception_raised = True
        # Should have multiple errors
        if len(err.errors) < 3:
            errmsg = f"Expected at least 3 errors, got {len(err.errors)}"
            raise AssertionError(errmsg)
    
    if exception_raised is not True:
        errmsg = "Expected ConfigurationError to be raised"
        raise AssertionError(errmsg)
    
    return


# =============================================================================
# Unit Tests for as_dict() and to_json()
# =============================================================================

def test_as_dict_returns_all_fields():
    """
        Test that as_dict returns all configuration fields.
    """
    config = ServerConfig(host="0.0.0.0", port=9000)
    
    result = config.as_dict()
    
    expected_fields = [
        "host", "port", "unix_socket", "backlog",
        "workers", "threads", "worker_class",
        "timeout", "keepalive", "graceful_timeout",
        "max_request_size", "max_header_size", "max_headers", "max_connections",
        "ssl_certfile", "ssl_keyfile", "ssl_ca_certs",
        "reload", "debug",
        "access_log", "error_log", "log_level"
    ]
    
    for field in expected_fields:
        if field not in result:
            errmsg = f"Expected field '{field}' in as_dict result"
            raise AssertionError(errmsg)
    
    if result["host"] != "0.0.0.0":
        errmsg = f"Expected host '0.0.0.0', got '{result['host']}'"
        raise AssertionError(errmsg)
    
    if result["port"] != 9000:
        errmsg = f"Expected port 9000, got {result['port']}"
        raise AssertionError(errmsg)
    
    return


def test_to_json_returns_valid_json():
    """
        Test that to_json returns valid JSON string.
    """
    config = ServerConfig(host="0.0.0.0", port=9000)
    
    json_str = config.to_json()
    
    # Should be parseable
    parsed = json.loads(json_str)
    
    if parsed["host"] != "0.0.0.0":
        errmsg = f"Expected host '0.0.0.0', got '{parsed['host']}'"
        raise AssertionError(errmsg)
    
    if parsed["port"] != 9000:
        errmsg = f"Expected port 9000, got {parsed['port']}"
        raise AssertionError(errmsg)
    
    return

