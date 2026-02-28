"""
.. module:: lifecycle
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: Application lifecycle integration for the configuration system.

.. moduleauthor:: Automation Mojo LLC

This module provides integration between the configuration system and the
application lifecycle, including persona system integration, eager validation,
and cleanup on shutdown.
"""

__author__ = "Automation Mojo LLC"
__copyright__ = "Copyright 2025, Automation Mojo LLC"
__credits__ = []


import atexit
import os
import sys
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, TYPE_CHECKING

from automojo.webworks.configuration.core import ConfigSourceType
from automojo.webworks.configuration.exceptions import (
    ConfigurationError,
    ConfigurationValidationError
)
from automojo.webworks.configuration.registry import ConfigRegistry
from automojo.webworks.configuration.schema import ConfigSchema
from automojo.webworks.configuration.sources import (
    ConfigFileDiscovery,
    EnvironmentSource,
    FileSource,
    ProfileConfigSource,
    SecretsProvider,
    DEFAULT_FILE_PATTERNS
)
from automojo.webworks.configuration.watcher import ConfigWatcher
from automojo.webworks.configuration.model import ConfigurationModel


if TYPE_CHECKING:
    from automojo.webworks.persona.webapplication import WebApplication


# Module-level registry for cleanup tracking
_ACTIVE_REGISTRIES: List['ManagedConfigRegistry'] = []


class ManagedConfigRegistry(ConfigRegistry):
    """
        A ConfigRegistry with lifecycle management capabilities.
        
        This class extends ConfigRegistry with support for:
        
        - Integration with the persona system for configuration discovery
        - Eager validation at startup
        - Proper cleanup on shutdown
        - File watching for configuration changes
        
        Example usage::
        
            from automojo.webworks.configuration.lifecycle import (
                ManagedConfigRegistry,
                create_config_from_persona
            )
            
            # Create from persona
            registry = create_config_from_persona()
            
            # Or create manually with lifecycle management
            registry = ManagedConfigRegistry(schema=my_schema)
            registry.setup_from_persona()
            registry.load()
            
            # Enable file watching
            registry.enable_watching()
            
            # Cleanup is automatic on shutdown, or call manually
            registry.cleanup()
        
        :param schema: Optional ConfigSchema for validation.
        :param precedence: Source precedence order (highest to lowest).
        :param enable_cleanup: Whether to register for automatic cleanup on shutdown.
    """
    
    def __init__(
        self,
        schema: Optional[ConfigSchema] = None,
        precedence: Optional[List[ConfigSourceType]] = None,
        enable_cleanup: bool = True
    ):
        """
            Initialize the ManagedConfigRegistry.
            
            :param schema: Optional schema for validation.
            :param precedence: Source precedence order (highest to lowest).
            :param enable_cleanup: Whether to register for automatic cleanup.
        """
        super().__init__(schema=schema, precedence=precedence)
        
        self._watcher: Optional[ConfigWatcher] = None
        self._secrets_provider: Optional[SecretsProvider] = None
        self._file_handles: List[Any] = []
        self._cleanup_callbacks: List[Callable[[], None]] = []
        self._cleaned_up = False
        
        if enable_cleanup:
            _ACTIVE_REGISTRIES.append(self)
    
    @property
    def watcher(self) -> Optional[ConfigWatcher]:
        """
            Get the configuration file watcher.
            
            :returns: The ConfigWatcher or None if not enabled.
        """
        return self._watcher
    
    @property
    def is_watching(self) -> bool:
        """
            Check if file watching is enabled and running.
            
            :returns: True if watching, False otherwise.
        """
        return self._watcher is not None and self._watcher.is_running
    
    def setup_from_persona(
        self,
        env_prefix: str = "APP_",
        secrets_env_prefix: str = "SECRET_",
        file_patterns: Optional[List[str]] = None,
        profile_env_var: str = "APP_PROFILE",
        include_system_dirs: bool = True
    ) -> 'ManagedConfigRegistry':
        """
            Set up configuration sources using the persona system.
            
            This method configures the registry to load configuration from:
            
            1. Environment variables with the specified prefix
            2. Configuration files in the presence directory
            3. Secrets from environment variables and/or encrypted files
            
            The presence directory is obtained from the persona system if
            available, otherwise falls back to the current directory.
            
            :param env_prefix: Prefix for environment variables.
            :param secrets_env_prefix: Prefix for secret environment variables.
            :param file_patterns: File name patterns to search for.
            :param profile_env_var: Environment variable for profile selection.
            :param include_system_dirs: Whether to include system directories.
            
            :returns: Self for method chaining.
        """
        # Get presence directory from persona system
        presence_dir = self._get_presence_directory()
        appname = self._get_app_name()
        
        # Build search directories
        search_directories = self._build_search_directories(
            presence_dir,
            appname,
            include_system_dirs
        )
        
        # Register environment source
        env_source = EnvironmentSource(prefix=env_prefix)
        self.register_source(env_source)
        
        # Register secrets provider
        self._secrets_provider = SecretsProvider(env_prefix=secrets_env_prefix)
        self.register_source(self._secrets_provider)
        
        # Register file source with discovery
        file_source = ProfileConfigSource(
            appname=appname,
            search_directories=search_directories,
            file_patterns=file_patterns or list(DEFAULT_FILE_PATTERNS),
            profile_env_var=profile_env_var
        )
        self.register_source(file_source)
        
        return self
    
    def _get_presence_directory(self) -> Path:
        """
            Get the presence directory from the persona system.
            
            :returns: The presence directory path.
        """
        try:
            from automojo.thisapp.persona import AppPersona
            
            presence_dir = AppPersona.AM_PRESENCE_DIR
            if presence_dir:
                # Expand user home and environment variables
                expanded = os.path.expanduser(os.path.expandvars(presence_dir))
                return Path(expanded)
        except (ImportError, AttributeError):
            pass
        
        # Fall back to current directory
        return Path.cwd()
    
    def _get_app_name(self) -> str:
        """
            Get the application name from the persona system.
            
            :returns: The application name.
        """
        try:
            from automojo.thisapp.persona import AppPersona
            
            name = AppPersona.AM_NAME
            if name:
                return name.lower()
        except (ImportError, AttributeError):
            pass
        
        # Fall back to "app"
        return "app"
    
    def _build_search_directories(
        self,
        presence_dir: Path,
        appname: str,
        include_system_dirs: bool
    ) -> List[str]:
        """
            Build the list of search directories for configuration files.
            
            :param presence_dir: The presence directory.
            :param appname: The application name.
            :param include_system_dirs: Whether to include system directories.
            
            :returns: List of directory path strings.
        """
        directories = [
            ".",                                    # Current directory
            "./config",                             # Config subdirectory
            str(presence_dir),                      # Presence directory
            str(presence_dir / "config"),           # Presence config subdirectory
        ]
        
        if include_system_dirs:
            directories.extend([
                f"~/.config/{appname}",             # User config directory
                f"/etc/{appname}",                  # System config directory
            ])
        
        return directories
    
    def enable_watching(
        self,
        poll_interval: float = 1.0,
        on_change: Optional[Callable[[Path], None]] = None
    ) -> 'ManagedConfigRegistry':
        """
            Enable file watching for configuration changes.
            
            This method creates a ConfigWatcher and starts monitoring
            all discovered configuration files for changes.
            
            :param poll_interval: Interval in seconds between file checks.
            :param on_change: Optional callback for file changes.
            
            :returns: Self for method chaining.
        """
        if self._watcher is not None:
            self._watcher.stop()
        
        self._watcher = ConfigWatcher(
            registry=self,
            poll_interval=poll_interval,
            on_change=on_change
        )
        
        # Add all file source paths to the watcher
        for source_type, sources in self._sources.items():
            if source_type == ConfigSourceType.FILE:
                for source in sources:
                    if hasattr(source, 'paths'):
                        for path in source.paths:
                            if path.exists():
                                self._watcher.watch(path)
                    elif hasattr(source, 'get_discovered_files'):
                        for path in source.get_discovered_files():
                            if path.exists():
                                self._watcher.watch(path)
        
        self._watcher.start()
        return self
    
    def disable_watching(self) -> 'ManagedConfigRegistry':
        """
            Disable file watching.
            
            :returns: Self for method chaining.
        """
        if self._watcher is not None:
            self._watcher.stop()
            self._watcher = None
        
        return self
    
    def on_cleanup(self, callback: Callable[[], None]) -> None:
        """
            Register a callback to be invoked during cleanup.
            
            :param callback: Callable to invoke during cleanup.
        """
        self._cleanup_callbacks.append(callback)
    
    def cleanup(self) -> None:
        """
            Clean up resources held by the registry.
            
            This method:
            
            - Stops the file watcher if running
            - Closes any open file handles
            - Invokes registered cleanup callbacks
            
            This method is safe to call multiple times.
        """
        if self._cleaned_up:
            return
        
        self._cleaned_up = True
        
        # Stop the watcher
        if self._watcher is not None:
            self._watcher.stop()
            self._watcher = None
        
        # Close file handles
        for handle in self._file_handles:
            try:
                if hasattr(handle, 'close'):
                    handle.close()
            except Exception:
                pass
        self._file_handles.clear()
        
        # Invoke cleanup callbacks
        for callback in self._cleanup_callbacks:
            try:
                callback()
            except Exception:
                pass
        self._cleanup_callbacks.clear()
        
        # Remove from active registries
        if self in _ACTIVE_REGISTRIES:
            _ACTIVE_REGISTRIES.remove(self)
    
    def __del__(self):
        """
            Destructor - ensure cleanup is called.
        """
        self.cleanup()


def validate_config_eagerly(
    registry: ConfigRegistry,
    exit_on_failure: bool = True
) -> List[str]:
    """
        Perform eager validation of all configuration at startup.
        
        This function validates all configuration values against the schema
        and returns a list of error messages. If exit_on_failure is True
        and validation fails, the process will exit with code 1.
        
        This is typically used with the --validate-config command-line option.
        
        :param registry: The ConfigRegistry to validate.
        :param exit_on_failure: Whether to exit the process on validation failure.
        
        :returns: List of validation error messages (empty if valid).
    """
    errors: List[str] = []
    
    try:
        # Force load with validation
        registry.load(validate=True)
    except ConfigurationValidationError as e:
        for error in e.errors:
            errors.append(f"{error.key}: {error.message}")
    except ConfigurationError as e:
        errors.append(str(e))
    
    if errors and exit_on_failure:
        print("Configuration validation failed:", file=sys.stderr)
        for error in errors:
            print(f"  - {error}", file=sys.stderr)
        sys.exit(1)
    
    return errors


def check_validate_config_flag() -> bool:
    """
        Check if the --validate-config flag is present in command-line arguments.
        
        :returns: True if --validate-config is present, False otherwise.
    """
    return "--validate-config" in sys.argv


def create_config_from_persona(
    schema: Optional[ConfigSchema] = None,
    env_prefix: str = "APP_",
    secrets_env_prefix: str = "SECRET_",
    file_patterns: Optional[List[str]] = None,
    profile_env_var: str = "APP_PROFILE",
    validate: bool = True,
    enable_watching: bool = False
) -> ManagedConfigRegistry:
    """
        Create a ManagedConfigRegistry configured from the persona system.
        
        This is a convenience function that creates a registry, sets it up
        using the persona system, and optionally loads and validates the
        configuration.
        
        Example usage::
        
            from automojo.webworks.configuration.lifecycle import create_config_from_persona
            
            # Basic usage
            registry = create_config_from_persona()
            
            # With custom schema
            schema = ConfigSchema()
            schema.define("database.host", str, default="localhost")
            registry = create_config_from_persona(schema=schema)
            
            # With file watching
            registry = create_config_from_persona(enable_watching=True)
        
        :param schema: Optional ConfigSchema for validation.
        :param env_prefix: Prefix for environment variables.
        :param secrets_env_prefix: Prefix for secret environment variables.
        :param file_patterns: File name patterns to search for.
        :param profile_env_var: Environment variable for profile selection.
        :param validate: Whether to validate configuration after loading.
        :param enable_watching: Whether to enable file watching.
        
        :returns: A configured ManagedConfigRegistry.
    """
    registry = ManagedConfigRegistry(schema=schema)
    
    registry.setup_from_persona(
        env_prefix=env_prefix,
        secrets_env_prefix=secrets_env_prefix,
        file_patterns=file_patterns,
        profile_env_var=profile_env_var
    )
    
    # Check for --validate-config flag
    if check_validate_config_flag():
        validate_config_eagerly(registry, exit_on_failure=True)
    else:
        registry.load(validate=validate)
    
    if enable_watching:
        registry.enable_watching()
    
    return registry


def cleanup_all_registries() -> None:
    """
        Clean up all active ManagedConfigRegistry instances.
        
        This function is registered with atexit to ensure proper cleanup
        when the application shuts down.
    """
    for registry in list(_ACTIVE_REGISTRIES):
        try:
            registry.cleanup()
        except Exception:
            pass


# Register cleanup handler
atexit.register(cleanup_all_registries)
