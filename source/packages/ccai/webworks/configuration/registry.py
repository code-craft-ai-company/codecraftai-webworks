"""
.. module:: registry
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: Configuration registry for managing sources, loading, and merging.

.. moduleauthor:: Code Craft AI LLC

This module contains the ConfigRegistry class which serves as the central
registry for managing configuration sources, loading configuration values,
and merging them according to precedence rules.
"""

__author__ = "Code Craft AI LLC"
__copyright__ = "Copyright 2025, Code Craft AI LLC"
__credits__ = []


import copy
import logging

from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple, Union

from ccai.webworks.configuration.core import (
    ConfigSourceType,
    ConfigValue,
    ConfigChangeEvent,
    SecretValue,
    ConfigKeyDefinition,
    DEFAULT_PRECEDENCE
)
from ccai.webworks.configuration.exceptions import (
    ConfigurationError,
    ConfigurationValidationError,
    ConfigurationFrozenError
)
from ccai.webworks.configuration.schema import ConfigSchema, coerce_value
from ccai.webworks.configuration.sources import (
    ConfigSource,
    ConfigLoader,
    FORMAT_LOADERS
)


# Module-level logger. Loader-init failures (missing optional deps
# like PyYAML / tomllib), failed change-callbacks, and the bare
# remove-callback-not-found path all leave breadcrumbs in the
# journal so the operator can correlate config behaviour with
# environment quirks.
logger = logging.getLogger(__name__)


class ConfigRegistry:
    """
        Central registry managing configuration sources, loading, and merging.
        
        The ConfigRegistry is responsible for:
        
        - Registering and managing configuration sources
        - Loading configuration from all sources
        - Merging values according to precedence order
        - Managing runtime overrides
        - Validating configuration against schema
        - Notifying callbacks on configuration changes
        - Freezing configuration to prevent modifications
        
        Example usage::
        
            from ccai.webworks.configuration import (
                ConfigRegistry,
                ConfigSchema,
                EnvironmentSource,
                FileSource
            )
            
            # Create schema
            schema = ConfigSchema()
            schema.define("database.host", str, default="localhost")
            schema.define("database.port", int, required=True)
            
            # Create registry
            registry = ConfigRegistry(schema=schema)
            
            # Register sources
            registry.register_source(EnvironmentSource(prefix="APP_"))
            registry.register_source(FileSource(paths=[Path("config.yaml")]))
            
            # Load configuration
            registry.load()
            
            # Access values
            host = registry.get("database.host")
            
            # Override at runtime
            registry.override("database.host", "db.example.com")
            
            # Freeze to prevent further changes
            registry.freeze()
        
        :param schema: Optional ConfigSchema for validation.
        :param precedence: Source precedence order (highest to lowest).
    """
    
    def __init__(
        self,
        schema: Optional[ConfigSchema] = None,
        precedence: Optional[List[ConfigSourceType]] = None,
        lazy: bool = False
    ):
        """
            Initialize the ConfigRegistry.
            
            :param schema: Optional schema for validation.
            :param precedence: Source precedence order (highest to lowest).
                             Defaults to DEFAULT_PRECEDENCE.
            :param lazy: If True, defer source loading until first access.
                        When lazy loading is enabled, calling load() will not
                        immediately load values from sources. Instead, values
                        are loaded on the first access (get, get_value, keys,
                        items, etc.).
        """
        self._schema = schema
        self._precedence = precedence if precedence is not None else list(DEFAULT_PRECEDENCE)
        self._sources: Dict[ConfigSourceType, List[ConfigSource]] = {}
        self._loaders: Dict[str, ConfigLoader] = {}
        self._overrides: Dict[str, Any] = {}
        self._callbacks: List[Callable[[ConfigChangeEvent], None]] = []
        self._frozen = False
        self._values: Dict[str, ConfigValue] = {}
        self._loaded = False
        self._lazy = lazy
        self._lazy_pending = False
        self._lazy_validate = True
        
        # Initialize loaders from FORMAT_LOADERS
        for fmt, loader_class in FORMAT_LOADERS.items():
            try:
                self._loaders[fmt] = loader_class()
            except ConfigurationError as exc:
                # Loader not available (e.g., YAML without PyYAML).
                # Log at debug — this is the expected outcome for
                # consumers that haven't installed the optional
                # extras, but the breadcrumb lets an operator
                # confirm "yaml file ignored because PyYAML missing"
                # without having to bisect the load path.
                logger.debug(
                    "ConfigRegistry: loader %s for format %r unavailable: %s",
                    loader_class.__name__,
                    fmt,
                    exc,
                )
    
    @property
    def schema(self) -> Optional[ConfigSchema]:
        """
            Get the configuration schema.
            
            :returns: The ConfigSchema or None if not set.
        """
        return self._schema
    
    @property
    def precedence(self) -> List[ConfigSourceType]:
        """
            Get the source precedence order.
            
            :returns: List of ConfigSourceType in precedence order.
        """
        return self._precedence
    
    @property
    def is_frozen(self) -> bool:
        """
            Check if the configuration is frozen.
            
            :returns: True if frozen, False otherwise.
        """
        return self._frozen
    
    @property
    def is_loaded(self) -> bool:
        """
            Check if configuration has been loaded.
            
            :returns: True if loaded, False otherwise.
        """
        return self._loaded

    @property
    def lazy(self) -> bool:
        """
            Check if lazy loading is enabled.
            
            :returns: True if lazy loading is enabled, False otherwise.
        """
        return self._lazy

    def _ensure_loaded(self) -> None:
        """
            Ensure configuration values are loaded from sources.
            
            When lazy loading is enabled, this method performs the deferred
            loading of source values on first access. If lazy loading is not
            enabled or values are already loaded, this is a no-op.
        """
        if self._lazy_pending:
            self._lazy_pending = False
            self._do_load(validate=self._lazy_validate)

    
    def register_source(self, source: ConfigSource) -> None:
        """
            Register a configuration source.
            
            Multiple sources of the same type can be registered. They will
            be loaded in the order they were registered, with later sources
            taking precedence for the same keys within that source type.
            
            :param source: The ConfigSource to register.
            
            :raises ConfigurationFrozenError: If configuration is frozen.
        """
        if self._frozen:
            raise ConfigurationFrozenError("sources")
        
        source_type = source.source_type
        if source_type not in self._sources:
            self._sources[source_type] = []
        
        self._sources[source_type].append(source)
    
    def register_loader(self, format: str, loader: ConfigLoader) -> None:
        """
            Register a custom configuration loader.
            
            This allows extending the registry with support for additional
            file formats beyond the built-in INI, YAML, JSON, and TOML.
            
            :param format: The format identifier (e.g., "xml", "properties").
            :param loader: The ConfigLoader instance.
            
            :raises ConfigurationFrozenError: If configuration is frozen.
        """
        if self._frozen:
            raise ConfigurationFrozenError("loaders")
        
        self._loaders[format] = loader
    
    def get_loader(self, format: str) -> Optional[ConfigLoader]:
        """
            Get a registered loader by format.
            
            :param format: The format identifier.
            
            :returns: The ConfigLoader or None if not registered.
        """
        return self._loaders.get(format)
    
    def load(self, validate: bool = True) -> 'ConfigRegistry':
        """
            Load configuration from all sources and merge according to precedence.
            
            This method loads configuration values from all registered sources,
            merges them according to the configured precedence order, and
            optionally validates against the schema.
            
            When lazy loading is enabled, this method defers the actual loading
            of source values until the first access. The registry is marked as
            loaded, but source values are not read until get(), get_value(),
            keys(), or items() is called.
            
            :param validate: Whether to validate against schema (default: True).
            
            :returns: Self for method chaining.
            
            :raises ConfigurationValidationError: If validation fails.
            :raises ConfigurationError: If loading fails.
        """
        if self._lazy:
            # Defer actual loading until first access
            self._lazy_pending = True
            self._lazy_validate = validate
            self._loaded = True
            return self
        
        self._do_load(validate=validate)
        return self
    
    def _do_load(self, validate: bool = True) -> None:
        """
            Perform the actual loading of configuration from all sources.
            
            This method contains the core loading logic, separated from load()
            to support lazy loading. It loads values from all registered sources,
            merges them according to precedence, and optionally validates.
            
            :param validate: Whether to validate against schema.
            
            :raises ConfigurationValidationError: If validation fails.
            :raises ConfigurationError: If loading fails.
        """
        # Clear existing values (but keep overrides)
        self._values.clear()
        
        # Collect all values from sources, organized by source type
        source_values: Dict[ConfigSourceType, Dict[str, Any]] = {}
        
        # Load from each source type in reverse precedence order
        # (so higher precedence sources overwrite lower ones)
        for source_type in reversed(self._precedence):
            if source_type == ConfigSourceType.OVERRIDE:
                # Overrides are handled separately
                continue
            
            if source_type == ConfigSourceType.DEFAULT:
                # Defaults come from schema
                if self._schema is not None:
                    source_values[source_type] = self._get_schema_defaults()
                continue
            
            if source_type in self._sources:
                merged: Dict[str, Any] = {}
                for source in self._sources[source_type]:
                    loaded = source.load()
                    merged.update(loaded)
                source_values[source_type] = merged
        
        # Merge values according to precedence (lower precedence first)
        merged_values: Dict[str, Tuple[Any, ConfigSourceType, str]] = {}
        
        for source_type in reversed(self._precedence):
            if source_type == ConfigSourceType.OVERRIDE:
                continue
            
            if source_type in source_values:
                for key, value in source_values[source_type].items():
                    source_detail = self._get_source_detail(source_type, key)
                    merged_values[key] = (value, source_type, source_detail)
        
        # Apply overrides (highest precedence)
        for key, value in self._overrides.items():
            source_detail = "OVERRIDE:programmatic"
            merged_values[key] = (value, ConfigSourceType.OVERRIDE, source_detail)
        
        # Create ConfigValue instances
        for key, (value, source_type, source_detail) in merged_values.items():
            is_sensitive = self._is_sensitive_key(key)
            is_override = source_type == ConfigSourceType.OVERRIDE
            
            self._values[key] = ConfigValue(
                key=key,
                value=value,
                source=source_type,
                source_detail=source_detail,
                is_override=is_override,
                is_sensitive=is_sensitive
            )
        
        # Validate if schema is provided and validation is requested
        if validate and self._schema is not None:
            self._validate()
        
        self._loaded = True
    
    def _get_schema_defaults(self) -> Dict[str, Any]:
        """
            Get default values from the schema.
            
            :returns: Dictionary of key to default value.
        """
        defaults: Dict[str, Any] = {}
        
        if self._schema is None:
            return defaults
        
        all_definitions = self._schema.get_all_definitions()
        for key, definition in all_definitions.items():
            if definition.default is not None:
                defaults[key] = definition.default
        
        return defaults
    
    def _get_source_detail(self, source_type: ConfigSourceType, key: str) -> str:
        """
            Get a source detail string for a key.
            
            :param source_type: The source type.
            :param key: The configuration key.
            
            :returns: A source detail string.
        """
        if source_type == ConfigSourceType.ENVIRONMENT:
            return f"ENV:{key.upper().replace('.', '_')}"
        elif source_type == ConfigSourceType.FILE:
            return f"FILE:config"
        elif source_type == ConfigSourceType.SECRETS:
            return f"SECRETS:{key}"
        elif source_type == ConfigSourceType.DEFAULT:
            return "DEFAULT:schema"
        elif source_type == ConfigSourceType.OVERRIDE:
            return "OVERRIDE:programmatic"
        else:
            return f"{source_type.name}:{key}"
    
    def _is_sensitive_key(self, key: str) -> bool:
        """
            Check if a key is marked as sensitive in the schema.
            
            :param key: The configuration key.
            
            :returns: True if sensitive, False otherwise.
        """
        if self._schema is None:
            return False
        
        definition = self._schema.get_definition(key)
        if definition is None:
            return False
        
        return definition.sensitive
    
    def _validate(self) -> None:
        """
            Validate configuration against the schema.
            
            :raises ConfigurationValidationError: If validation fails.
        """
        if self._schema is None:
            return
        
        # Convert ConfigValue dict to plain values dict
        values_dict = self._build_nested_dict()
        
        errors = self._schema.validate(values_dict)
        if errors:
            raise ConfigurationValidationError(errors)
    
    def _build_nested_dict(self) -> Dict[str, Any]:
        """
            Build a nested dictionary from flat ConfigValue entries.
            
            :returns: Nested dictionary of configuration values.
        """
        result: Dict[str, Any] = {}
        
        for key, config_value in self._values.items():
            parts = key.split(".")
            current = result
            
            for i, part in enumerate(parts[:-1]):
                if part not in current:
                    current[part] = {}
                elif not isinstance(current[part], dict):
                    # Handle case where a key is both a value and a parent
                    current[part] = {"": current[part]}
                current = current[part]
            
            # Get the actual value (unwrap SecretValue if needed for validation)
            value = config_value.value
            if isinstance(value, SecretValue):
                value = value.get_secret_value()
            
            current[parts[-1]] = value
        
        return result

    
    def get(self, key: str, default: Any = None) -> Any:
        """
            Get a configuration value by key.
            
            :param key: The configuration key in dot-notation.
            :param default: Default value if key not found.
            
            :returns: The configuration value or default.
        """
        if not self._loaded:
            self.load()
        
        self._ensure_loaded()
        
        if key in self._values:
            return self._values[key].value
        
        return default
    
    def get_value(self, key: str) -> Optional[ConfigValue]:
        """
            Get a ConfigValue by key.
            
            :param key: The configuration key.
            
            :returns: The ConfigValue or None if not found.
        """
        if not self._loaded:
            self.load()
        
        self._ensure_loaded()
        
        return self._values.get(key)
    
    def keys(self) -> List[str]:
        """
            Get all configuration keys.
            
            :returns: List of configuration keys.
        """
        if not self._loaded:
            self.load()
        
        self._ensure_loaded()
        
        return list(self._values.keys())
    
    def items(self) -> List[Tuple[str, Any]]:
        """
            Get all configuration key-value pairs.
            
            :returns: List of (key, value) tuples.
        """
        if not self._loaded:
            self.load()
        
        self._ensure_loaded()
        
        return [(k, v.value) for k, v in self._values.items()]
    
    def override(self, key: str, value: Any) -> None:
        """
            Set a programmatic override for a configuration key.
            
            Overrides take the highest precedence and will be used instead
            of values from any other source.
            
            :param key: The configuration key.
            :param value: The override value.
            
            :raises ConfigurationFrozenError: If configuration is frozen.
        """
        if self._frozen:
            raise ConfigurationFrozenError(key)
        
        # Get old value for change notification
        old_value = None
        if key in self._values:
            old_value = self._values[key].value
        elif key in self._overrides:
            old_value = self._overrides[key]
        
        # Store the override
        self._overrides[key] = value
        
        # Update the values dict if already loaded
        if self._loaded:
            is_sensitive = self._is_sensitive_key(key)
            self._values[key] = ConfigValue(
                key=key,
                value=value,
                source=ConfigSourceType.OVERRIDE,
                source_detail="OVERRIDE:programmatic",
                is_override=True,
                is_sensitive=is_sensitive
            )
        
        # Fire change notification
        if old_value != value:
            self._fire_change_event(key, old_value, value, ConfigSourceType.OVERRIDE)
    
    def clear_override(self, key: str) -> None:
        """
            Clear a programmatic override for a configuration key.
            
            After clearing, the value will be resolved from other sources
            according to precedence.
            
            :param key: The configuration key.
            
            :raises ConfigurationFrozenError: If configuration is frozen.
        """
        if self._frozen:
            raise ConfigurationFrozenError(key)
        
        if key in self._overrides:
            old_value = self._overrides[key]
            del self._overrides[key]
            
            # Reload to get the value from other sources
            if self._loaded:
                self.load(validate=False)
                new_value = self._values.get(key)
                new_val = new_value.value if new_value else None
                self._fire_change_event(key, old_value, new_val, ConfigSourceType.OVERRIDE)
    
    def clear_all_overrides(self) -> None:
        """
            Clear all programmatic overrides.
            
            :raises ConfigurationFrozenError: If configuration is frozen.
        """
        if self._frozen:
            raise ConfigurationFrozenError("overrides")
        
        self._overrides.clear()
        
        if self._loaded:
            self.load(validate=False)
    
    def freeze(self) -> None:
        """
            Freeze configuration to prevent further modifications.
            
            Once frozen, any attempt to modify the configuration (via override,
            register_source, etc.) will raise ConfigurationFrozenError.
        """
        self._frozen = True
    
    def on_change(self, callback: Callable[[ConfigChangeEvent], None]) -> None:
        """
            Register a callback for configuration change notifications.
            
            The callback will be invoked whenever a configuration value
            changes, receiving a ConfigChangeEvent with details about
            the change.
            
            :param callback: Callable that accepts a ConfigChangeEvent.
        """
        self._callbacks.append(callback)
    
    def remove_change_callback(self, callback: Callable[[ConfigChangeEvent], None]) -> bool:
        """
            Remove a previously registered change callback.
            
            :param callback: The callback to remove.
            
            :returns: True if callback was found and removed, False otherwise.
        """
        try:
            self._callbacks.remove(callback)
            return True
        except ValueError:
            return False
    
    def _fire_change_event(
        self,
        key: str,
        old_value: Any,
        new_value: Any,
        source: ConfigSourceType
    ) -> None:
        """
            Fire a change event to all registered callbacks.
            
            :param key: The configuration key that changed.
            :param old_value: The previous value.
            :param new_value: The new value.
            :param source: The source of the change.
        """
        event = ConfigChangeEvent(
            key=key,
            old_value=old_value,
            new_value=new_value,
            source=source,
            timestamp=datetime.now(timezone.utc)
        )
        
        for callback in self._callbacks:
            try:
                callback(event)
            except Exception:
                # Don't let callback errors break the registry — but
                # do surface them in the journal so a misbehaving
                # subscriber doesn't silently corrupt downstream
                # state.
                logger.exception(
                    "ConfigRegistry: change-event callback %r raised for key=%s",
                    callback,
                    key,
                )
    
    def update(self, values: Dict[str, Any], atomic: bool = True) -> None:
        """
            Update multiple configuration values atomically.
            
            When atomic=True, either all updates succeed or none do.
            This ensures configuration consistency.
            
            :param values: Dictionary of key-value pairs to update.
            :param atomic: Whether to apply updates atomically (default: True).
            
            :raises ConfigurationFrozenError: If configuration is frozen.
            :raises ConfigurationValidationError: If validation fails (atomic mode).
        """
        if self._frozen:
            raise ConfigurationFrozenError("update")
        
        if atomic:
            self._atomic_update(values)
        else:
            for key, value in values.items():
                self.override(key, value)
    
    def _atomic_update(self, values: Dict[str, Any]) -> None:
        """
            Perform an atomic update of multiple values.
            
            :param values: Dictionary of key-value pairs to update.
            
            :raises ConfigurationValidationError: If validation fails.
        """
        # Save current state
        old_overrides = copy.deepcopy(self._overrides)
        old_values = copy.deepcopy(self._values)
        
        try:
            # Apply all updates
            for key, value in values.items():
                self._overrides[key] = value
            
            # Reload and validate
            self.load(validate=True)
            
            # Fire change events for successful updates
            for key, value in values.items():
                old_value = None
                if key in old_values:
                    old_value = old_values[key].value
                elif key in old_overrides:
                    old_value = old_overrides[key]
                
                if old_value != value:
                    self._fire_change_event(key, old_value, value, ConfigSourceType.OVERRIDE)
                    
        except (ConfigurationValidationError, ConfigurationError):
            # Rollback on failure
            self._overrides = old_overrides
            self._values = old_values
            raise
    
    # =========================================================================
    # Export Functionality
    # =========================================================================
    
    def export(
        self,
        format: str,
        path: Optional[Path] = None,
        mask_secrets: bool = True
    ) -> Optional[str]:
        """
            Export configuration to a file format.
            
            This method exports the current configuration values to the specified
            format (INI, YAML, JSON, TOML). Sensitive values are masked by default
            to prevent accidental exposure.
            
            :param format: Output format (ini, yaml, json, toml).
            :param path: Optional file path to write to. If not provided,
                        returns the configuration as a string.
            :param mask_secrets: Whether to mask sensitive values (default: True).
            
            :returns: Configuration string if path not provided, None otherwise.
            
            :raises ConfigurationError: If format is not supported or export fails.
        """
        if not self._loaded:
            self.load()
        
        # Get the loader for the format
        format_lower = format.lower()
        loader = self.get_loader(format_lower)
        
        if loader is None:
            raise ConfigurationError(f"Unsupported export format: {format}")
        
        # Build the export data
        export_data = self._build_export_data(mask_secrets=mask_secrets)
        
        # Serialize using the loader
        content = loader.dump(export_data)
        
        # Write to file or return string
        if path is not None:
            path = Path(path) if isinstance(path, str) else path
            path.write_text(content)
            return None
        
        return content
    
    def _build_export_data(self, mask_secrets: bool = True) -> Dict[str, Any]:
        """
            Build a dictionary of configuration values for export.
            
            :param mask_secrets: Whether to mask sensitive values.
            
            :returns: Dictionary of configuration key-value pairs.
        """
        result: Dict[str, Any] = {}
        
        for key, config_value in self._values.items():
            value = config_value.value
            
            # Handle SecretValue wrapper
            if isinstance(value, SecretValue):
                if mask_secrets:
                    value = SecretValue.MASKED_VALUE
                else:
                    value = value.get_secret_value()
            elif config_value.is_sensitive and mask_secrets:
                value = SecretValue.MASKED_VALUE
            
            result[key] = value
        
        return result
    
    def export_template(self, format: str) -> str:
        """
            Export a configuration template with defaults and descriptions.
            
            This method generates a template configuration file that includes
            all defined keys with their default values and descriptions as
            comments. This is useful for generating example configuration files.
            
            :param format: Output format (ini, yaml, json, toml).
            
            :returns: The template configuration string.
            
            :raises ConfigurationError: If format is not supported or no schema defined.
        """
        if self._schema is None:
            raise ConfigurationError(
                "Cannot export template without a schema definition"
            )
        
        format_lower = format.lower()
        
        # Build template data from schema
        template_data: Dict[str, Any] = {}
        all_definitions = self._schema.get_all_definitions()
        
        for key, definition in all_definitions.items():
            # Use default value or a placeholder
            if definition.default is not None:
                value = definition.default
            elif definition.type is str:
                value = ""
            elif definition.type is int:
                value = 0
            elif definition.type is float:
                value = 0.0
            elif definition.type is bool:
                value = False
            elif definition.type is list:
                value = []
            elif definition.type is dict:
                value = {}
            else:
                value = None
            
            # Mask sensitive values in template
            if definition.sensitive:
                value = SecretValue.MASKED_VALUE
            
            template_data[key] = value
        
        # Generate format-specific template with comments
        if format_lower == "yaml":
            return self._export_yaml_template(template_data, all_definitions)
        elif format_lower == "json":
            return self._export_json_template(template_data, all_definitions)
        elif format_lower in ("ini", "cfg", "conf"):
            return self._export_ini_template(template_data, all_definitions)
        elif format_lower == "toml":
            return self._export_toml_template(template_data, all_definitions)
        else:
            raise ConfigurationError(f"Unsupported template format: {format}")
    
    def _export_yaml_template(
        self,
        data: Dict[str, Any],
        definitions: Dict[str, 'ConfigKeyDefinition']
    ) -> str:
        """
            Export a YAML template with comments.
            
            :param data: Template data.
            :param definitions: Key definitions for comments.
            
            :returns: YAML template string.
        """
        from ccai.webworks.configuration.sources import _unflatten_dict
        
        lines = ["# Configuration Template", "# Generated from schema", ""]
        
        # Group keys by top-level namespace
        nested = _unflatten_dict(data)
        
        def write_yaml_section(obj: Any, indent: int = 0, parent_key: str = "") -> List[str]:
            result = []
            prefix = "  " * indent
            
            if isinstance(obj, dict):
                for key, value in obj.items():
                    full_key = f"{parent_key}.{key}" if parent_key else key
                    definition = definitions.get(full_key)
                    
                    # Add description comment
                    if definition and definition.description:
                        result.append(f"{prefix}# {definition.description}")
                    
                    # Add type and required info
                    if definition:
                        type_info = f"Type: {definition.type.__name__}"
                        if definition.required:
                            type_info += ", Required"
                        if definition.choices:
                            type_info += f", Choices: {definition.choices}"
                        result.append(f"{prefix}# {type_info}")
                    
                    if isinstance(value, dict):
                        result.append(f"{prefix}{key}:")
                        result.extend(write_yaml_section(value, indent + 1, full_key))
                    else:
                        yaml_value = self._format_yaml_value(value)
                        result.append(f"{prefix}{key}: {yaml_value}")
                    
                    result.append("")  # Blank line between entries
            
            return result
        
        lines.extend(write_yaml_section(nested))
        return "\n".join(lines)
    
    def _format_yaml_value(self, value: Any) -> str:
        """
            Format a value for YAML output.
            
            :param value: The value to format.
            
            :returns: YAML-formatted string.
        """
        if value is None:
            return "null"
        elif isinstance(value, bool):
            return "true" if value else "false"
        elif isinstance(value, str):
            if value == "" or any(c in value for c in ":#{}[]&*!|>'\"%@`"):
                return f'"{value}"'
            return value
        elif isinstance(value, (list, dict)):
            import json
            return json.dumps(value)
        else:
            return str(value)
    
    def _export_json_template(
        self,
        data: Dict[str, Any],
        definitions: Dict[str, 'ConfigKeyDefinition']
    ) -> str:
        """
            Export a JSON template (JSON doesn't support comments, so we add
            description fields).
            
            :param data: Template data.
            :param definitions: Key definitions.
            
            :returns: JSON template string.
        """
        import json
        from ccai.webworks.configuration.sources import _unflatten_dict
        
        nested = _unflatten_dict(data)
        return json.dumps(nested, indent=2)
    
    def _export_ini_template(
        self,
        data: Dict[str, Any],
        definitions: Dict[str, 'ConfigKeyDefinition']
    ) -> str:
        """
            Export an INI template with comments.
            
            :param data: Template data.
            :param definitions: Key definitions for comments.
            
            :returns: INI template string.
        """
        lines = ["; Configuration Template", "; Generated from schema", ""]
        
        # Group keys by section (first part of dot-notation)
        sections: Dict[str, Dict[str, Any]] = {}
        defaults: Dict[str, Any] = {}
        
        for key, value in data.items():
            if "." in key:
                parts = key.split(".", 1)
                section = parts[0]
                subkey = parts[1]
                if section not in sections:
                    sections[section] = {}
                sections[section][subkey] = (value, key)
            else:
                defaults[key] = (value, key)
        
        # Write defaults section
        if defaults:
            lines.append("[DEFAULT]")
            for key, (value, full_key) in defaults.items():
                definition = definitions.get(full_key)
                if definition and definition.description:
                    lines.append(f"; {definition.description}")
                if definition:
                    type_info = f"; Type: {definition.type.__name__}"
                    if definition.required:
                        type_info += ", Required"
                    lines.append(type_info)
                lines.append(f"{key} = {value}")
                lines.append("")
        
        # Write sections
        for section, items in sorted(sections.items()):
            lines.append(f"[{section}]")
            for subkey, (value, full_key) in items.items():
                definition = definitions.get(full_key)
                if definition and definition.description:
                    lines.append(f"; {definition.description}")
                if definition:
                    type_info = f"; Type: {definition.type.__name__}"
                    if definition.required:
                        type_info += ", Required"
                    lines.append(type_info)
                lines.append(f"{subkey} = {value}")
                lines.append("")
        
        return "\n".join(lines)
    
    def _export_toml_template(
        self,
        data: Dict[str, Any],
        definitions: Dict[str, 'ConfigKeyDefinition']
    ) -> str:
        """
            Export a TOML template with comments.
            
            :param data: Template data.
            :param definitions: Key definitions for comments.
            
            :returns: TOML template string.
        """
        lines = ["# Configuration Template", "# Generated from schema", ""]
        
        # Group keys by section
        sections: Dict[str, Dict[str, Any]] = {}
        top_level: Dict[str, Any] = {}
        
        for key, value in data.items():
            if "." in key:
                parts = key.split(".", 1)
                section = parts[0]
                subkey = parts[1]
                if section not in sections:
                    sections[section] = {}
                sections[section][subkey] = (value, key)
            else:
                top_level[key] = (value, key)
        
        # Write top-level keys
        for key, (value, full_key) in top_level.items():
            definition = definitions.get(full_key)
            if definition and definition.description:
                lines.append(f"# {definition.description}")
            if definition:
                type_info = f"# Type: {definition.type.__name__}"
                if definition.required:
                    type_info += ", Required"
                lines.append(type_info)
            lines.append(f"{key} = {self._format_toml_value(value)}")
            lines.append("")
        
        # Write sections
        for section, items in sorted(sections.items()):
            lines.append(f"[{section}]")
            for subkey, (value, full_key) in items.items():
                definition = definitions.get(full_key)
                if definition and definition.description:
                    lines.append(f"# {definition.description}")
                if definition:
                    type_info = f"# Type: {definition.type.__name__}"
                    if definition.required:
                        type_info += ", Required"
                    lines.append(type_info)
                lines.append(f"{subkey} = {self._format_toml_value(value)}")
                lines.append("")
        
        return "\n".join(lines)
    
    def _format_toml_value(self, value: Any) -> str:
        """
            Format a value for TOML output.
            
            :param value: The value to format.
            
            :returns: TOML-formatted string.
        """
        if value is None:
            return '""'
        elif isinstance(value, bool):
            return "true" if value else "false"
        elif isinstance(value, str):
            # TOML strings need to be quoted
            escaped = value.replace("\\", "\\\\").replace('"', '\\"')
            return f'"{escaped}"'
        elif isinstance(value, (int, float)):
            return str(value)
        elif isinstance(value, list):
            items = [self._format_toml_value(v) for v in value]
            return f"[{', '.join(items)}]"
        elif isinstance(value, dict):
            # TOML inline tables
            items = [f"{k} = {self._format_toml_value(v)}" for k, v in value.items()]
            return f"{{ {', '.join(items)} }}"
        else:
            return f'"{value}"'
    
    def export_documentation(self) -> str:
        """
            Generate documentation for all configuration keys.
            
            This method generates human-readable documentation for all
            configuration keys defined in the schema, including:
            
            - Key name
            - Type
            - Default value
            - Description
            - Required status
            - Choices (if enum constraint)
            
            :returns: Markdown-formatted documentation string.
            
            :raises ConfigurationError: If no schema is defined.
        """
        if self._schema is None:
            raise ConfigurationError(
                "Cannot export documentation without a schema definition"
            )
        
        lines = [
            "# Configuration Documentation",
            "",
            "This document describes all available configuration options.",
            "",
        ]
        
        all_definitions = self._schema.get_all_definitions()
        
        # Group by namespace
        namespaces: Dict[str, List[tuple]] = {}
        
        for key, definition in sorted(all_definitions.items()):
            if "." in key:
                namespace = key.split(".")[0]
            else:
                namespace = "General"
            
            if namespace not in namespaces:
                namespaces[namespace] = []
            namespaces[namespace].append((key, definition))
        
        # Generate documentation for each namespace
        for namespace, items in sorted(namespaces.items()):
            lines.append(f"## {namespace.title()}")
            lines.append("")
            
            for key, definition in items:
                lines.append(f"### `{key}`")
                lines.append("")
                
                if definition.description:
                    lines.append(definition.description)
                    lines.append("")
                
                lines.append(f"- **Type:** `{definition.type.__name__}`")
                lines.append(f"- **Required:** {'Yes' if definition.required else 'No'}")
                
                if definition.default is not None:
                    default_str = repr(definition.default)
                    lines.append(f"- **Default:** `{default_str}`")
                
                if definition.choices:
                    choices_str = ", ".join(repr(c) for c in definition.choices)
                    lines.append(f"- **Choices:** {choices_str}")
                
                if definition.sensitive:
                    lines.append("- **Sensitive:** Yes (value will be masked)")
                
                lines.append("")
        
        return "\n".join(lines)
    
    def export_diff(self) -> Dict[str, tuple]:
        """
            Export diff between current configuration and defaults.
            
            This method returns a dictionary containing only the keys whose
            current values differ from their schema defaults.
            
            :returns: Dictionary mapping keys to (current_value, default_value) tuples.
            
            :raises ConfigurationError: If no schema is defined.
        """
        if self._schema is None:
            raise ConfigurationError(
                "Cannot export diff without a schema definition"
            )
        
        if not self._loaded:
            self.load()
        
        diff: Dict[str, tuple] = {}
        all_definitions = self._schema.get_all_definitions()
        
        for key, definition in all_definitions.items():
            default_value = definition.default
            current_value = self.get(key, None)
            
            # Handle SecretValue wrapper
            if isinstance(current_value, SecretValue):
                current_value = current_value.get_secret_value()
            
            # Compare values
            if current_value != default_value:
                diff[key] = (current_value, default_value)
        
        # Also include keys that are in values but not in schema
        for key in self._values.keys():
            if key not in all_definitions and key not in diff:
                current_value = self._values[key].value
                if isinstance(current_value, SecretValue):
                    current_value = current_value.get_secret_value()
                diff[key] = (current_value, None)
        
        return diff
