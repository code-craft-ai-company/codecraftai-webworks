"""
.. module:: model
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: Configuration model providing unified access to configuration values.

.. moduleauthor:: Code Craft AI LLC

This module contains the ConfigurationModel class which provides a unified
access point for all configuration values with typed access methods,
dot-notation access, dictionary-style access, and namespace groupings.
"""

__author__ = "Code Craft AI LLC"
__copyright__ = "Copyright 2025, Code Craft AI LLC"
__credits__ = []


from typing import Any, Dict, List, Optional, TYPE_CHECKING

from ccai.webworks.configuration.core import (
    ConfigValue,
    ConfigValueMetadata,
    ConfigSourceType,
)
from ccai.webworks.configuration.exceptions import (
    ConfigurationError,
    ConfigurationTypeError
)
from ccai.webworks.configuration.schema import coerce_value

if TYPE_CHECKING:
    from ccai.webworks.configuration.registry import ConfigRegistry


# Sentinel value for missing defaults
_MISSING = object()


class ConfigNamespace:
    """
        A namespace view of configuration providing scoped access.
        
        ConfigNamespace provides access to a subset of configuration keys
        under a common prefix. It supports the same access patterns as
        ConfigurationModel but scoped to the namespace prefix.
        
        Example usage::
        
            # Get a namespace for database configuration
            db = config.namespace("database")
            
            # Access values within the namespace
            host = db.get("host")  # Equivalent to config.get("database.host")
            port = db.get_int("port")  # Equivalent to config.get_int("database.port")
        
        :param model: The parent ConfigurationModel.
        :param prefix: The namespace prefix (e.g., "database").
    """
    
    def __init__(self, model: 'ConfigurationModel', prefix: str):
        """
            Initialize the ConfigNamespace.
            
            :param model: The parent ConfigurationModel.
            :param prefix: The namespace prefix.
        """
        self._model = model
        self._prefix = prefix
    
    @property
    def prefix(self) -> str:
        """
            Get the namespace prefix.
            
            :returns: The namespace prefix string.
        """
        return self._prefix
    
    def _full_key(self, key: str) -> str:
        """
            Get the full key by prepending the namespace prefix.
            
            :param key: The relative key within the namespace.
            
            :returns: The full key with prefix.
        """
        if key:
            return f"{self._prefix}.{key}"
        return self._prefix
    
    def get(self, key: str, default: Any = _MISSING) -> Any:
        """
            Get a configuration value by key within this namespace.
            
            :param key: The relative key within the namespace.
            :param default: Default value if key not found.
            
            :returns: The configuration value or default.
            
            :raises ConfigurationError: If key not found and no default provided.
        """
        return self._model.get(self._full_key(key), default)
    
    def get_str(self, key: str, default: Optional[str] = None) -> str:
        """
            Get a string configuration value within this namespace.
            
            :param key: The relative key within the namespace.
            :param default: Default value if key not found.
            
            :returns: The string value.
        """
        return self._model.get_str(self._full_key(key), default)
    
    def get_int(self, key: str, default: Optional[int] = None) -> int:
        """
            Get an integer configuration value within this namespace.
            
            :param key: The relative key within the namespace.
            :param default: Default value if key not found.
            
            :returns: The integer value.
        """
        return self._model.get_int(self._full_key(key), default)
    
    def get_float(self, key: str, default: Optional[float] = None) -> float:
        """
            Get a float configuration value within this namespace.
            
            :param key: The relative key within the namespace.
            :param default: Default value if key not found.
            
            :returns: The float value.
        """
        return self._model.get_float(self._full_key(key), default)
    
    def get_bool(self, key: str, default: Optional[bool] = None) -> bool:
        """
            Get a boolean configuration value within this namespace.
            
            :param key: The relative key within the namespace.
            :param default: Default value if key not found.
            
            :returns: The boolean value.
        """
        return self._model.get_bool(self._full_key(key), default)
    
    def get_list(self, key: str, default: Optional[List] = None) -> List:
        """
            Get a list configuration value within this namespace.
            
            :param key: The relative key within the namespace.
            :param default: Default value if key not found.
            
            :returns: The list value.
        """
        return self._model.get_list(self._full_key(key), default)
    
    def get_dict(self, key: str, default: Optional[Dict] = None) -> Dict:
        """
            Get a dictionary configuration value within this namespace.
            
            :param key: The relative key within the namespace.
            :param default: Default value if key not found.
            
            :returns: The dictionary value.
        """
        return self._model.get_dict(self._full_key(key), default)
    
    def get_metadata(self, key: str) -> ConfigValueMetadata:
        """
            Get metadata about a configuration value within this namespace.
            
            :param key: The relative key within the namespace.
            
            :returns: Metadata including source and override status.
        """
        return self._model.get_metadata(self._full_key(key))
    
    def namespace(self, prefix: str) -> 'ConfigNamespace':
        """
            Get a nested namespace view.
            
            :param prefix: The nested namespace prefix.
            
            :returns: A ConfigNamespace for the nested prefix.
        """
        return ConfigNamespace(self._model, self._full_key(prefix))
    
    def __getattr__(self, name: str) -> Any:
        """
            Support dot-notation access within the namespace.
            
            :param name: The attribute name (configuration key).
            
            :returns: The configuration value or a nested ConfigNamespace.
        """
        full_key = self._full_key(name)
        
        # Check if this is a leaf value or a namespace
        if self._model._has_key(full_key):
            return self._model.get(full_key)
        
        # Check if there are keys with this prefix
        if self._model._has_prefix(full_key):
            return ConfigNamespace(self._model, full_key)
        
        raise AttributeError(f"Configuration key '{full_key}' not found")
    
    def __getitem__(self, key: str) -> Any:
        """
            Support dictionary-style access within the namespace.
            
            :param key: The configuration key.
            
            :returns: The configuration value or a nested ConfigNamespace.
        """
        full_key = self._full_key(key)
        
        # Check if this is a leaf value
        if self._model._has_key(full_key):
            return self._model.get(full_key)
        
        # Check if there are keys with this prefix (namespace)
        if self._model._has_prefix(full_key):
            return ConfigNamespace(self._model, full_key)
        
        raise KeyError(f"Configuration key '{full_key}' not found")



class ConfigurationModel:
    """
        Unified access point for all configuration values.
        
        The ConfigurationModel provides a consistent API for accessing
        configuration values regardless of their source. It supports:
        
        - Typed access methods (get_str, get_int, get_float, get_bool, get_list, get_dict)
        - Dot-notation access (config.database.host)
        - Dictionary-style access (config["database"]["host"])
        - Namespace groupings for organizing related settings
        - Value metadata including source and override status
        
        Example usage::
        
            from ccai.webworks.configuration import ConfigRegistry, ConfigSchema
            
            # Create and configure registry
            schema = ConfigSchema()
            schema.define("database.host", str, default="localhost")
            schema.define("database.port", int, required=True)
            
            registry = ConfigRegistry(schema=schema)
            registry.load()
            
            # Create model from registry
            config = ConfigurationModel(registry)
            
            # Typed access
            host = config.get_str("database.host")
            port = config.get_int("database.port")
            
            # Dot-notation access
            host = config.database.host
            
            # Dictionary-style access
            host = config["database"]["host"]
            
            # Namespace grouping
            db = config.namespace("database")
            host = db.get("host")
        
        :param registry: The ConfigRegistry providing resolved values.
    """
    
    def __init__(self, registry: 'ConfigRegistry'):
        """
            Initialize the ConfigurationModel.
            
            :param registry: The ConfigRegistry providing resolved values.
        """
        self._registry = registry
        self._cache: Dict[str, ConfigValue] = {}
    
    @property
    def registry(self) -> 'ConfigRegistry':
        """
            Get the underlying ConfigRegistry.
            
            :returns: The ConfigRegistry instance.
        """
        return self._registry
    
    def _ensure_loaded(self) -> None:
        """
            Ensure the registry has loaded configuration.
        """
        if not self._registry.is_loaded:
            self._registry.load()
    
    def _get_config_value(self, key: str) -> Optional[ConfigValue]:
        """
            Get a ConfigValue from the registry.
            
            :param key: The configuration key.
            
            :returns: The ConfigValue or None if not found.
        """
        self._ensure_loaded()
        return self._registry.get_value(key)
    
    def _has_key(self, key: str) -> bool:
        """
            Check if a key exists in the configuration.
            
            :param key: The configuration key.
            
            :returns: True if the key exists, False otherwise.
        """
        self._ensure_loaded()
        return key in self._registry.keys()
    
    def _has_prefix(self, prefix: str) -> bool:
        """
            Check if any keys exist with the given prefix.
            
            :param prefix: The key prefix to check.
            
            :returns: True if any keys have this prefix, False otherwise.
        """
        self._ensure_loaded()
        prefix_dot = prefix + "."
        for key in self._registry.keys():
            if key.startswith(prefix_dot):
                return True
        return False
    
    def get(self, key: str, default: Any = _MISSING) -> Any:
        """
            Get a configuration value by key.
            
            :param key: Dot-notation key (e.g., "database.host").
            :param default: Default value if key not found.
            
            :returns: The configuration value.
            
            :raises ConfigurationError: If key not found and no default provided.
        """
        self._ensure_loaded()
        
        config_value = self._get_config_value(key)
        
        if config_value is not None:
            return config_value.value
        
        # Check if there's a schema default
        if self._registry.schema is not None:
            definition = self._registry.schema.get_definition(key)
            if definition is not None and definition.default is not None:
                return definition.default
        
        # Return provided default or raise error
        if default is not _MISSING:
            return default
        
        # Check if key is required in schema
        if self._registry.schema is not None:
            definition = self._registry.schema.get_definition(key)
            if definition is not None and definition.required:
                raise ConfigurationError(
                    f"Required configuration key '{key}' is missing",
                    key=key
                )
        
        raise ConfigurationError(
            f"Configuration key '{key}' not found and no default provided",
            key=key
        )
    
    def get_str(self, key: str, default: Optional[str] = None) -> str:
        """
            Get a string configuration value.
            
            :param key: The configuration key.
            :param default: Default value if key not found.
            
            :returns: The string value.
            
            :raises ConfigurationTypeError: If value cannot be coerced to string.
        """
        try:
            value = self.get(key, default)
            if value is None:
                if default is not None:
                    return default
                raise ConfigurationError(
                    f"Configuration key '{key}' resolved to None and no non-None default provided",
                    key=key
                )
            return coerce_value(value, str)
        except (ValueError, TypeError) as e:
            raise ConfigurationTypeError(key, str, value) from e
    
    def get_int(self, key: str, default: Optional[int] = None) -> int:
        """
            Get an integer configuration value.
            
            :param key: The configuration key.
            :param default: Default value if key not found.
            
            :returns: The integer value.
            
            :raises ConfigurationTypeError: If value cannot be coerced to int.
        """
        try:
            value = self.get(key, default)
            if value is None:
                if default is not None:
                    return default
                raise ConfigurationError(
                    f"Configuration key '{key}' resolved to None and no non-None default provided",
                    key=key
                )
            return coerce_value(value, int)
        except (ValueError, TypeError) as e:
            raise ConfigurationTypeError(key, int, value) from e
    
    def get_float(self, key: str, default: Optional[float] = None) -> float:
        """
            Get a float configuration value.
            
            :param key: The configuration key.
            :param default: Default value if key not found.
            
            :returns: The float value.
            
            :raises ConfigurationTypeError: If value cannot be coerced to float.
        """
        try:
            value = self.get(key, default)
            if value is None:
                if default is not None:
                    return default
                raise ConfigurationError(
                    f"Configuration key '{key}' resolved to None and no non-None default provided",
                    key=key
                )
            return coerce_value(value, float)
        except (ValueError, TypeError) as e:
            raise ConfigurationTypeError(key, float, value) from e
    
    def get_bool(self, key: str, default: Optional[bool] = None) -> bool:
        """
            Get a boolean configuration value.
            
            :param key: The configuration key.
            :param default: Default value if key not found.
            
            :returns: The boolean value.
            
            :raises ConfigurationTypeError: If value cannot be coerced to bool.
        """
        try:
            value = self.get(key, default)
            if value is None:
                if default is not None:
                    return default
                raise ConfigurationError(
                    f"Configuration key '{key}' resolved to None and no non-None default provided",
                    key=key
                )
            return coerce_value(value, bool)
        except (ValueError, TypeError) as e:
            raise ConfigurationTypeError(key, bool, value) from e
    
    def get_list(self, key: str, default: Optional[List] = None) -> List:
        """
            Get a list configuration value.
            
            :param key: The configuration key.
            :param default: Default value if key not found.
            
            :returns: The list value.
            
            :raises ConfigurationTypeError: If value cannot be coerced to list.
        """
        try:
            value = self.get(key, default)
            if value is None:
                if default is not None:
                    return default
                raise ConfigurationError(
                    f"Configuration key '{key}' resolved to None and no non-None default provided",
                    key=key
                )
            return coerce_value(value, list)
        except (ValueError, TypeError) as e:
            raise ConfigurationTypeError(key, list, value) from e
    
    def get_dict(self, key: str, default: Optional[Dict] = None) -> Dict:
        """
            Get a dictionary configuration value.
            
            :param key: The configuration key.
            :param default: Default value if key not found.
            
            :returns: The dictionary value.
            
            :raises ConfigurationTypeError: If value cannot be coerced to dict.
        """
        try:
            value = self.get(key, default)
            if value is None:
                if default is not None:
                    return default
                raise ConfigurationError(
                    f"Configuration key '{key}' resolved to None and no non-None default provided",
                    key=key
                )
            return coerce_value(value, dict)
        except (ValueError, TypeError) as e:
            raise ConfigurationTypeError(key, dict, value) from e
    
    def get_metadata(self, key: str) -> ConfigValueMetadata:
        """
            Get metadata about a configuration value.
            
            :param key: The configuration key.
            
            :returns: Metadata including source and override status.
            
            :raises ConfigurationError: If key not found.
        """
        self._ensure_loaded()
        
        config_value = self._get_config_value(key)
        
        # Get schema info if available
        schema_type = None
        schema_default = None
        schema_description = ""
        
        if self._registry.schema is not None:
            definition = self._registry.schema.get_definition(key)
            if definition is not None:
                schema_type = definition.type
                schema_default = definition.default
                schema_description = definition.description
        
        if config_value is not None:
            return ConfigValueMetadata(
                source=config_value.source,
                source_detail=config_value.source_detail,
                is_override=config_value.is_override,
                is_sensitive=config_value.is_sensitive,
                schema_type=schema_type,
                schema_default=schema_default,
                schema_description=schema_description
            )
        
        # Key not found in values, but might have schema default
        if schema_default is not None:
            return ConfigValueMetadata(
                source=ConfigSourceType.DEFAULT,
                source_detail="DEFAULT:schema",
                is_override=False,
                is_sensitive=False,
                schema_type=schema_type,
                schema_default=schema_default,
                schema_description=schema_description
            )
        
        raise ConfigurationError(
            f"Configuration key '{key}' not found",
            key=key
        )
    
    def namespace(self, prefix: str) -> ConfigNamespace:
        """
            Get a namespace view of configuration.
            
            :param prefix: The namespace prefix (e.g., "database").
            
            :returns: A ConfigNamespace providing scoped access.
        """
        return ConfigNamespace(self, prefix)
    
    def keys(self) -> List[str]:
        """
            Get all configuration keys.
            
            :returns: List of configuration keys.
        """
        self._ensure_loaded()
        return self._registry.keys()
    
    def items(self) -> List[tuple]:
        """
            Get all configuration key-value pairs.
            
            :returns: List of (key, value) tuples.
        """
        self._ensure_loaded()
        return self._registry.items()
    
    def __getattr__(self, name: str) -> Any:
        """
            Support dot-notation access (config.database.host).
            
            :param name: The attribute name (configuration key).
            
            :returns: The configuration value or a ConfigNamespace for nested access.
        """
        # Avoid recursion for private attributes
        if name.startswith("_"):
            raise AttributeError(f"'{type(self).__name__}' object has no attribute '{name}'")
        
        # Check if this is a leaf value
        if self._has_key(name):
            return self.get(name)
        
        # Check if there are keys with this prefix (namespace)
        if self._has_prefix(name):
            return ConfigNamespace(self, name)
        
        raise AttributeError(f"Configuration key '{name}' not found")
    
    def __getitem__(self, key: str) -> Any:
        """
            Support dictionary-style access (config["database"]["host"]).
            
            :param key: The configuration key.
            
            :returns: The configuration value or a ConfigNamespace for nested access.
        """
        # Check if this is a leaf value
        if self._has_key(key):
            return self.get(key)
        
        # Check if there are keys with this prefix (namespace)
        if self._has_prefix(key):
            return ConfigNamespace(self, key)
        
        raise KeyError(f"Configuration key '{key}' not found")
    
    def __contains__(self, key: str) -> bool:
        """
            Check if a key exists in the configuration.
            
            :param key: The configuration key.
            
            :returns: True if the key exists, False otherwise.
        """
        return self._has_key(key)
    
    def __repr__(self) -> str:
        """
            Return a string representation of the ConfigurationModel.
            
            :returns: String representation.
        """
        self._ensure_loaded()
        key_count = len(self._registry.keys())
        return f"ConfigurationModel(keys={key_count})"
