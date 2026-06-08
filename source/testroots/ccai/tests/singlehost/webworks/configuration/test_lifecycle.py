"""
    Tests for the configuration lifecycle module.
    
    This module contains unit tests for the lifecycle integration including
    ManagedConfigRegistry, persona integration, eager validation, and cleanup.
"""

import os
import sys
import tempfile
from pathlib import Path


# =============================================================================
# Unit Tests for ManagedConfigRegistry
# =============================================================================

def test_managed_config_registry_creation():
    """
        Test that ManagedConfigRegistry can be created.
    """
    from ccai.webworks.configuration.lifecycle import ManagedConfigRegistry
    from ccai.webworks.configuration.schema import ConfigSchema
    
    # Create without schema
    registry = ManagedConfigRegistry(enable_cleanup=False)
    
    if registry is None:
        raise AssertionError("Expected registry to be created")
    
    if registry.is_frozen:
        raise AssertionError("Expected registry to not be frozen")
    
    if registry.is_loaded:
        raise AssertionError("Expected registry to not be loaded")
    
    # Create with schema
    schema = ConfigSchema()
    schema.define("test.key", str, default="value")
    
    registry_with_schema = ManagedConfigRegistry(schema=schema, enable_cleanup=False)
    
    if registry_with_schema.schema is None:
        raise AssertionError("Expected registry to have schema")
    
    return


def test_managed_config_registry_setup_from_persona():
    """
        Test that setup_from_persona configures sources correctly.
    """
    from ccai.webworks.configuration.lifecycle import ManagedConfigRegistry
    from ccai.webworks.configuration.core import ConfigSourceType
    
    registry = ManagedConfigRegistry(enable_cleanup=False)
    
    # Setup from persona (will use fallback values since persona not established)
    result = registry.setup_from_persona(
        env_prefix="TEST_",
        secrets_env_prefix="TESTSECRET_"
    )
    
    # Should return self for chaining
    if result is not registry:
        raise AssertionError("Expected setup_from_persona to return self")
    
    # Should have registered sources
    if ConfigSourceType.ENVIRONMENT not in registry._sources:
        raise AssertionError("Expected ENVIRONMENT source to be registered")
    
    if ConfigSourceType.SECRETS not in registry._sources:
        raise AssertionError("Expected SECRETS source to be registered")
    
    if ConfigSourceType.FILE not in registry._sources:
        raise AssertionError("Expected FILE source to be registered")
    
    return


def test_managed_config_registry_load():
    """
        Test that ManagedConfigRegistry can load configuration.
    """
    from ccai.webworks.configuration.lifecycle import ManagedConfigRegistry
    from ccai.webworks.configuration.schema import ConfigSchema
    
    schema = ConfigSchema()
    schema.define("test.key", str, default="default_value")
    
    registry = ManagedConfigRegistry(schema=schema, enable_cleanup=False)
    registry.setup_from_persona()
    registry.load()
    
    if not registry.is_loaded:
        raise AssertionError("Expected registry to be loaded")
    
    # Should be able to get the default value
    value = registry.get("test.key")
    
    if value != "default_value":
        raise AssertionError(f"Expected 'default_value', got {value}")
    
    return


def test_managed_config_registry_cleanup():
    """
        Test that cleanup properly releases resources.
    """
    from ccai.webworks.configuration.lifecycle import ManagedConfigRegistry
    
    registry = ManagedConfigRegistry(enable_cleanup=False)
    
    # Track cleanup callback
    cleanup_called = [False]
    
    def cleanup_callback():
        cleanup_called[0] = True
    
    registry.on_cleanup(cleanup_callback)
    
    # Cleanup should invoke callback
    registry.cleanup()
    
    if not cleanup_called[0]:
        raise AssertionError("Expected cleanup callback to be called")
    
    if not registry._cleaned_up:
        raise AssertionError("Expected registry to be marked as cleaned up")
    
    # Multiple cleanup calls should be safe
    registry.cleanup()
    
    return


def test_managed_config_registry_enable_watching():
    """
        Test that file watching can be enabled and disabled.
    """
    from ccai.webworks.configuration.lifecycle import ManagedConfigRegistry
    
    registry = ManagedConfigRegistry(enable_cleanup=False)
    registry.setup_from_persona()
    registry.load()
    
    # Enable watching
    result = registry.enable_watching(poll_interval=0.5)
    
    if result is not registry:
        raise AssertionError("Expected enable_watching to return self")
    
    if not registry.is_watching:
        raise AssertionError("Expected registry to be watching")
    
    if registry.watcher is None:
        raise AssertionError("Expected watcher to be set")
    
    # Disable watching
    result = registry.disable_watching()
    
    if result is not registry:
        raise AssertionError("Expected disable_watching to return self")
    
    if registry.is_watching:
        raise AssertionError("Expected registry to not be watching")
    
    if registry.watcher is not None:
        raise AssertionError("Expected watcher to be None")
    
    return


def test_validate_config_eagerly_success():
    """
        Test eager validation with valid configuration.
    """
    from ccai.webworks.configuration.lifecycle import (
        ManagedConfigRegistry,
        validate_config_eagerly
    )
    from ccai.webworks.configuration.schema import ConfigSchema
    
    schema = ConfigSchema()
    schema.define("test.key", str, default="value")
    
    registry = ManagedConfigRegistry(schema=schema, enable_cleanup=False)
    registry.setup_from_persona()
    
    # Should return empty list for valid config
    errors = validate_config_eagerly(registry, exit_on_failure=False)
    
    if len(errors) != 0:
        raise AssertionError(f"Expected no errors, got {errors}")
    
    return


def test_validate_config_eagerly_failure():
    """
        Test eager validation with invalid configuration.
    """
    from ccai.webworks.configuration.lifecycle import (
        ManagedConfigRegistry,
        validate_config_eagerly
    )
    from ccai.webworks.configuration.schema import ConfigSchema
    
    schema = ConfigSchema()
    schema.define("required.key", str, required=True)  # Required but not provided
    
    registry = ManagedConfigRegistry(schema=schema, enable_cleanup=False)
    registry.setup_from_persona()
    
    # Should return errors for missing required key
    errors = validate_config_eagerly(registry, exit_on_failure=False)
    
    if len(errors) == 0:
        raise AssertionError("Expected validation errors for missing required key")
    
    return


def test_check_validate_config_flag():
    """
        Test detection of --validate-config flag.
    """
    from ccai.webworks.configuration.lifecycle import check_validate_config_flag
    
    # Save original argv
    original_argv = sys.argv.copy()
    
    try:
        # Without flag
        sys.argv = ["test_program"]
        
        if check_validate_config_flag():
            raise AssertionError("Expected False without --validate-config flag")
        
        # With flag
        sys.argv = ["test_program", "--validate-config"]
        
        if not check_validate_config_flag():
            raise AssertionError("Expected True with --validate-config flag")
        
        # With flag among other args
        sys.argv = ["test_program", "--other", "--validate-config", "--more"]
        
        if not check_validate_config_flag():
            raise AssertionError("Expected True with --validate-config among other args")
    finally:
        # Restore original argv
        sys.argv = original_argv
    
    return


def test_create_config_from_persona():
    """
        Test the convenience function for creating config from persona.
    """
    from ccai.webworks.configuration.lifecycle import (
        create_config_from_persona,
        _ACTIVE_REGISTRIES
    )
    from ccai.webworks.configuration.schema import ConfigSchema
    
    schema = ConfigSchema()
    schema.define("test.key", str, default="value")
    
    # Create registry
    registry = create_config_from_persona(
        schema=schema,
        validate=True,
        enable_watching=False
    )
    
    if registry is None:
        raise AssertionError("Expected registry to be created")
    
    if not registry.is_loaded:
        raise AssertionError("Expected registry to be loaded")
    
    if registry not in _ACTIVE_REGISTRIES:
        raise AssertionError("Expected registry to be in active registries")
    
    # Cleanup
    registry.cleanup()
    
    if registry in _ACTIVE_REGISTRIES:
        raise AssertionError("Expected registry to be removed from active registries")
    
    return


def test_cleanup_all_registries():
    """
        Test that cleanup_all_registries cleans up all active registries.
    """
    from ccai.webworks.configuration.lifecycle import (
        ManagedConfigRegistry,
        cleanup_all_registries,
        _ACTIVE_REGISTRIES
    )
    
    # Create multiple registries
    registry1 = ManagedConfigRegistry(enable_cleanup=True)
    registry2 = ManagedConfigRegistry(enable_cleanup=True)
    
    if registry1 not in _ACTIVE_REGISTRIES:
        raise AssertionError("Expected registry1 to be in active registries")
    
    if registry2 not in _ACTIVE_REGISTRIES:
        raise AssertionError("Expected registry2 to be in active registries")
    
    # Cleanup all
    cleanup_all_registries()
    
    if registry1 in _ACTIVE_REGISTRIES:
        raise AssertionError("Expected registry1 to be removed from active registries")
    
    if registry2 in _ACTIVE_REGISTRIES:
        raise AssertionError("Expected registry2 to be removed from active registries")
    
    if not registry1._cleaned_up:
        raise AssertionError("Expected registry1 to be cleaned up")
    
    if not registry2._cleaned_up:
        raise AssertionError("Expected registry2 to be cleaned up")
    
    return


def test_managed_config_registry_with_env_vars():
    """
        Test that environment variables are loaded correctly.
    """
    from ccai.webworks.configuration.lifecycle import ManagedConfigRegistry
    from ccai.webworks.configuration.schema import ConfigSchema
    
    # Set up test environment variable
    os.environ["TESTAPP_DATABASE_HOST"] = "testhost.example.com"
    
    try:
        schema = ConfigSchema()
        schema.define("database.host", str, default="localhost")
        
        registry = ManagedConfigRegistry(schema=schema, enable_cleanup=False)
        registry.setup_from_persona(env_prefix="TESTAPP_")
        registry.load()
        
        # Should get value from environment
        value = registry.get("database.host")
        
        if value != "testhost.example.com":
            raise AssertionError(f"Expected 'testhost.example.com', got {value}")
    finally:
        # Clean up environment
        del os.environ["TESTAPP_DATABASE_HOST"]
    
    return


def test_managed_config_registry_with_config_file():
    """
        Test that configuration files are loaded correctly.
    """
    from ccai.webworks.configuration.lifecycle import ManagedConfigRegistry
    from ccai.webworks.configuration.schema import ConfigSchema
    from ccai.webworks.configuration.sources import FileSource
    
    # Create a temporary config file
    with tempfile.NamedTemporaryFile(
        mode='w',
        suffix='.json',
        delete=False
    ) as f:
        f.write('{"database": {"host": "filehost.example.com", "port": 5432}}')
        config_path = Path(f.name)
    
    try:
        schema = ConfigSchema()
        schema.define("database.host", str, default="localhost")
        schema.define("database.port", int, default=3306)
        
        registry = ManagedConfigRegistry(schema=schema, enable_cleanup=False)
        
        # Register file source directly
        file_source = FileSource(paths=[config_path])
        registry.register_source(file_source)
        registry.load()
        
        # Should get values from file
        host = registry.get("database.host")
        port = registry.get("database.port")
        
        if host != "filehost.example.com":
            raise AssertionError(f"Expected 'filehost.example.com', got {host}")
        
        if port != 5432:
            raise AssertionError(f"Expected 5432, got {port}")
    finally:
        # Clean up temp file
        config_path.unlink()
    
    return


def test_managed_config_registry_presence_directory_fallback():
    """
        Test that presence directory is retrieved (either from persona or fallback).
    """
    from ccai.webworks.configuration.lifecycle import ManagedConfigRegistry
    
    registry = ManagedConfigRegistry(enable_cleanup=False)
    
    # Get presence directory - may be from persona or fallback to cwd
    presence_dir = registry._get_presence_directory()
    
    # Should return a valid Path
    if not isinstance(presence_dir, Path):
        raise AssertionError(f"Expected Path, got {type(presence_dir)}")
    
    # Get app name - may be from persona or fallback to "app"
    app_name = registry._get_app_name()
    
    # Should return a non-empty string
    if not isinstance(app_name, str) or len(app_name) == 0:
        raise AssertionError(f"Expected non-empty string, got {app_name}")
    
    return


def test_managed_config_registry_build_search_directories():
    """
        Test that search directories are built correctly.
    """
    from ccai.webworks.configuration.lifecycle import ManagedConfigRegistry
    
    registry = ManagedConfigRegistry(enable_cleanup=False)
    
    presence_dir = Path("/test/presence")
    appname = "testapp"
    
    # With system dirs
    dirs = registry._build_search_directories(presence_dir, appname, True)
    
    if "." not in dirs:
        raise AssertionError("Expected '.' in search directories")
    
    if "./config" not in dirs:
        raise AssertionError("Expected './config' in search directories")
    
    if str(presence_dir) not in dirs:
        raise AssertionError(f"Expected '{presence_dir}' in search directories")
    
    if str(presence_dir / "config") not in dirs:
        raise AssertionError(f"Expected '{presence_dir / 'config'}' in search directories")
    
    if f"~/.config/{appname}" not in dirs:
        raise AssertionError(f"Expected '~/.config/{appname}' in search directories")
    
    if f"/etc/{appname}" not in dirs:
        raise AssertionError(f"Expected '/etc/{appname}' in search directories")
    
    # Without system dirs
    dirs_no_sys = registry._build_search_directories(presence_dir, appname, False)
    
    if "." not in dirs_no_sys:
        raise AssertionError("Expected '.' in search directories without system dirs")
    
    if f"/etc/{appname}" in dirs_no_sys:
        raise AssertionError(f"Expected '/etc/{appname}' NOT in search directories without system dirs")
    
    return

