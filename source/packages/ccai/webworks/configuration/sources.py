"""
.. module:: sources
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: Configuration source implementations for loading configuration values.

.. moduleauthor:: Code Craft AI LLC

This module contains the abstract ConfigSource base class and concrete implementations
for loading configuration from various sources including environment variables,
files, and secrets providers.
"""

__author__ = "Code Craft AI LLC"
__copyright__ = "Copyright 2025, Code Craft AI LLC"
__credits__ = []


import configparser
import json
import logging
import os
import re

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Set, Tuple, Union

from ccai.webworks.configuration.core import ConfigSourceType, SecretValue
from ccai.webworks.configuration.exceptions import (
    ConfigurationError,
    ConfigurationFileNotFoundError
)


# Module-level logger. Source loaders translate parser exceptions
# into ``ConfigurationError`` for the caller, but the operator wants
# the journal to carry the original parse failure so a malformed
# YAML / TOML / INI file is debuggable without re-running the load.
logger = logging.getLogger(__name__)


class ConfigSource(ABC):
    """
        Abstract base class for configuration sources.
        
        This class defines the interface that all configuration sources must
        implement. Configuration sources are responsible for loading configuration
        values from their respective backends (environment variables, files,
        secrets stores, etc.).
        
        Subclasses must implement:
        
        - load(): Load and return configuration values as a dictionary
        - source_type: Property returning the ConfigSourceType for precedence ordering
        
        Example implementation::
        
            class MyCustomSource(ConfigSource):
                
                def load(self) -> Dict[str, Any]:
                    return {"my.key": "my_value"}
                
                @property
                def source_type(self) -> ConfigSourceType:
                    return ConfigSourceType.FILE
    """
    
    @abstractmethod
    def load(self) -> Dict[str, Any]:
        """
            Load configuration values from this source.
            
            This method should read configuration from the source's backend
            and return a dictionary of key-value pairs. Keys should use
            dot-notation for nested values (e.g., "database.host").
            
            :returns: Dictionary of configuration key-value pairs.
            
            :raises ConfigurationError: If loading fails due to source-specific errors.
        """
        pass
    
    @property
    @abstractmethod
    def source_type(self) -> ConfigSourceType:
        """
            Return the source type for precedence ordering.
            
            This property is used by the ConfigRegistry to determine the
            precedence of values from this source when merging configuration
            from multiple sources.
            
            :returns: The ConfigSourceType for this source.
        """
        pass
    
    def use_known_keys(self, keys: List[str]) -> None:
        """
            Tell the source which configuration keys the schema defines.
            
            The ConfigRegistry calls this before each load. A source that
            derives key names from something that cannot spell them exactly,
            such as environment variable names, uses the keys to pick the
            intended one. The default implementation ignores them.
            
            :param keys: The keys defined by the registry's schema; empty when
                         the registry has no schema.
        """
        return


def _build_known_key_lookup(keys: List[str], separator: str, lowercase_keys: bool) -> Dict[str, Optional[str]]:
    """
        Index configuration keys by the key an environment variable name
        would naively be turned into.
        
        An environment variable cannot tell the separator inside a key name
        from the separator between nesting levels: ``DATABASE_MAX_CONNECTIONS``
        naively becomes ``database.max.connections``. The index maps that
        naive key back to the key that was meant, ``database.max_connections``.
        
        :param keys: The known configuration keys.
        :param separator: The separator used in environment variable names.
        :param lowercase_keys: Whether derived keys are lowercased.
        
        :returns: Dictionary of naive key to known key. The value is None
                  when more than one known key has the same naive form, so
                  the name cannot be resolved.
    """
    lookup: Dict[str, Optional[str]] = {}
    
    for key in keys:
        naive_key = key.replace(separator, ".")
        if lowercase_keys:
            naive_key = naive_key.lower()
        
        if naive_key not in lookup:
            lookup[naive_key] = key
        elif lookup[naive_key] != key:
            logger.warning(
                "Configuration keys %r and %r are spelled the same as an environment variable; "
                "use a doubled separator in the variable name to say which is meant",
                lookup[naive_key],
                key,
            )
            lookup[naive_key] = None
    
    return lookup


def _environment_name_to_key(
    name: str,
    separator: str,
    lowercase_keys: bool,
    known_keys: Dict[str, Optional[str]]
) -> str:
    """
        Turn an environment variable name, prefix already removed, into a
        configuration key.
        
        - A name that contains the separator doubled uses the doubled
          separator between nesting levels and keeps single separators as
          part of the key names: ``DATABASE__MAX_CONNECTIONS`` is
          ``database.max_connections``.
        - Otherwise every separator becomes a dot (``DATABASE_HOST`` is
          ``database.host``), and when exactly one known key is spelled
          that way as an environment variable, that key is used:
          ``DATABASE_MAX_CONNECTIONS`` is ``database.max_connections`` when
          the schema defines it.
        
        :param name: The environment variable name without its prefix.
        :param separator: The separator used in environment variable names.
        :param lowercase_keys: Whether to lowercase the resulting key.
        :param known_keys: Index built by :func:`_build_known_key_lookup`.
        
        :returns: The configuration key.
    """
    doubled_separator = separator + separator
    
    if len(separator) > 0 and doubled_separator in name:
        key = name.replace(doubled_separator, ".")
        if lowercase_keys:
            key = key.lower()
        return key
    
    key = name.replace(separator, ".")
    if lowercase_keys:
        key = key.lower()
    
    if key in known_keys:
        known_key = known_keys[key]
        if known_key is not None:
            key = known_key
    
    return key


class ConfigLoader(ABC):
    """
        Abstract base class for configuration format loaders.
        
        This class defines the interface that all configuration format loaders
        must implement. Configuration loaders are responsible for parsing
        configuration content from a specific format (INI, YAML, JSON, TOML)
        into a dictionary of key-value pairs.
        
        Subclasses must implement:
        
        - load(content: str): Parse content string and return configuration dictionary
        - dump(data: Dict[str, Any]): Serialize configuration dictionary to string
        
        Example implementation::
        
            class MyFormatLoader(ConfigLoader):
                
                def load(self, content: str) -> Dict[str, Any]:
                    # Parse content and return dictionary
                    return {"my.key": "my_value"}
                
                def dump(self, data: Dict[str, Any]) -> str:
                    # Serialize dictionary to string
                    return "my.key=my_value"
    """
    
    @abstractmethod
    def load(self, content: str) -> Dict[str, Any]:
        """
            Parse configuration content and return a dictionary.
            
            This method should parse the content string in the loader's
            format and return a dictionary of key-value pairs. Keys should
            use dot-notation for nested values (e.g., "database.host").
            
            :param content: The configuration content string to parse.
            
            :returns: Dictionary of configuration key-value pairs.
            
            :raises ConfigurationError: If parsing fails.
        """
        pass
    
    @abstractmethod
    def dump(self, data: Dict[str, Any]) -> str:
        """
            Serialize configuration dictionary to a string.
            
            This method should serialize the configuration dictionary
            to a string in the loader's format.
            
            :param data: Dictionary of configuration key-value pairs.
            
            :returns: The serialized configuration string.
            
            :raises ConfigurationError: If serialization fails.
        """
        pass


class EnvironmentSource(ConfigSource):
    """
        Configuration source that reads from environment variables.
        
        This source loads configuration values from environment variables,
        supporting prefix-based filtering and key mapping. Environment variable
        names are transformed to configuration keys using the following rules:
        
        1. Remove the prefix (e.g., "APP_")
        2. Replace the separator (e.g., "_") with dots
        3. Optionally lowercase the resulting key
        
        Example transformations (with prefix="APP_", separator="_", lowercase=True):
        
        - APP_DATABASE_HOST -> database.host
        - APP_DATABASE_PORT -> database.port
        - APP_LOG_LEVEL -> log.level
        
        A key whose own name contains the separator can be reached in two
        ways. When the registry has a schema, a variable name is matched
        to the schema key it spells: with ``database.max_connections``
        defined, APP_DATABASE_MAX_CONNECTIONS sets that key rather than
        ``database.max.connections``. With or without a schema, a doubled
        separator marks the nesting levels explicitly and leaves single
        separators in the key: APP_DATABASE__MAX_CONNECTIONS is
        ``database.max_connections``.
        
        :param prefix: Environment variable prefix to filter by (e.g., "APP_").
                      Only variables starting with this prefix will be loaded.
        :param separator: Separator character in environment variable names that
                         maps to dots in configuration keys (default: "_").
        :param lowercase_keys: Whether to lowercase the resulting configuration
                              keys (default: True).
    """
    
    def __init__(
        self,
        prefix: str = "APP_",
        separator: str = "_",
        lowercase_keys: bool = True
    ):
        """
            Initialize the EnvironmentSource.
            
            :param prefix: Environment variable prefix (e.g., "APP_").
            :param separator: Separator for nested keys (e.g., "_" for APP_DATABASE_HOST).
            :param lowercase_keys: Whether to lowercase resulting keys.
        """
        self._prefix = prefix
        self._separator = separator
        self._lowercase_keys = lowercase_keys
        self._known_keys: Dict[str, Optional[str]] = {}
    
    def use_known_keys(self, keys: List[str]) -> None:
        """
            Remember the keys the schema defines, so a variable name is
            mapped to the schema key it spells.
            
            :param keys: The keys defined by the registry's schema.
        """
        self._known_keys = _build_known_key_lookup(keys, self._separator, self._lowercase_keys)
        return
    
    @property
    def prefix(self) -> str:
        """
            Get the environment variable prefix.
            
            :returns: The prefix string.
        """
        return self._prefix
    
    @property
    def separator(self) -> str:
        """
            Get the separator character.
            
            :returns: The separator string.
        """
        return self._separator
    
    @property
    def lowercase_keys(self) -> bool:
        """
            Get whether keys are lowercased.
            
            :returns: True if keys are lowercased, False otherwise.
        """
        return self._lowercase_keys
    
    @property
    def source_type(self) -> ConfigSourceType:
        """
            Return the source type for precedence ordering.
            
            :returns: ConfigSourceType.ENVIRONMENT
        """
        return ConfigSourceType.ENVIRONMENT
    
    def load(self) -> Dict[str, Any]:
        """
            Load configuration from environment variables.
            
            This method reads all environment variables that start with the
            configured prefix, transforms their names to configuration keys,
            and returns them as a dictionary.
            
            :returns: Dictionary of configuration key-value pairs.
        """
        result: Dict[str, Any] = {}
        
        for env_name, env_value in os.environ.items():
            # Check if the variable starts with our prefix
            if not env_name.startswith(self._prefix):
                continue
            
            # Transform the environment variable name to a configuration key
            config_key = self._transform_env_name(env_name)
            
            # Store the value
            result[config_key] = env_value
        
        return result
    
    def _transform_env_name(self, env_name: str) -> str:
        """
            Transform an environment variable name to a configuration key.
            
            This method removes the prefix, replaces separators with dots,
            and optionally lowercases the result. A doubled separator marks
            the nesting levels explicitly, and a name that spells a key of
            the schema is mapped to that key; see
            :func:`_environment_name_to_key`.
            
            :param env_name: The environment variable name.
            
            :returns: The transformed configuration key.
        """
        # Remove the prefix
        name = env_name[len(self._prefix):]
        
        key = _environment_name_to_key(name, self._separator, self._lowercase_keys, self._known_keys)
        return key
    
    def transform_key_to_env_name(self, config_key: str) -> str:
        """
            Transform a configuration key to an environment variable name.
            
            This is the inverse of _transform_env_name and is useful for
            documentation and debugging purposes.
            
            :param config_key: The configuration key (e.g., "database.host").
            
            :returns: The environment variable name (e.g., "APP_DATABASE_HOST").
        """
        # Replace dots with separator
        env_name = config_key.replace(".", self._separator)
        
        # Uppercase if we lowercase keys (inverse operation)
        if self._lowercase_keys:
            env_name = env_name.upper()
        
        # Add prefix
        return self._prefix + env_name


# A section name that cannot be written in an INI file (a section header is
# a single line). IniLoader gives it to the parser as the name of its
# defaults section so that no section of the file is treated as defaults.
INI_UNUSED_DEFAULT_SECTION = "webworks\nno-defaults-section"


class IniLoader(ConfigLoader):
    """
        Configuration loader for INI format files.
        
        This loader parses INI format configuration files using Python's
        configparser module. Section names are used to create nested keys
        using dot-notation.
        
        Example INI content::
        
            [database]
            host = localhost
            port = 5432
            
            [logging]
            level = DEBUG
        
        Results in::
        
            {
                "database.host": "localhost",
                "database.port": "5432",
                "logging.level": "DEBUG"
            }
        
        The DEFAULT section (if present) creates top-level keys without
        a section prefix. Its keys are not copied into the other sections.
        
        Values are literal text: ``%`` has no special meaning.
    """
    
    def load(self, content: str) -> Dict[str, Any]:
        """
            Parse INI format content and return a dictionary.
            
            Section names become key prefixes using dot-notation.
            Values in the DEFAULT section become top-level keys.
            
            :param content: The INI format content string to parse.
            
            :returns: Dictionary of configuration key-value pairs.
            
            :raises ConfigurationError: If parsing fails.
        """
        # Values are taken literally: with interpolation a "%" in a value,
        # as in a password, is a syntax error. The parser is also told to
        # look for its defaults in a section that cannot exist, so
        # [DEFAULT] is read as a section like any other and each section
        # lists exactly the keys written in it. With the usual handling a
        # key written in a section could not be told from one inherited
        # from [DEFAULT], and a section's own value for such a key was lost.
        parser = configparser.ConfigParser(
            interpolation=None,
            default_section=INI_UNUSED_DEFAULT_SECTION
        )
        
        try:
            parser.read_string(content)
        except configparser.Error as e:
            logger.warning("INI loader: parse failure: %s", e)
            raise ConfigurationError(f"Failed to parse INI content: {e}") from e
        
        result: Dict[str, Any] = {}
        
        for section in parser.sections():
            for key, value in parser.items(section):
                if section == configparser.DEFAULTSECT:
                    # DEFAULT section (top-level keys)
                    result[key] = value
                else:
                    # Create dot-notation key
                    full_key = f"{section}.{key}"
                    result[full_key] = value
        
        return result
    
    def dump(self, data: Dict[str, Any]) -> str:
        """
            Serialize configuration dictionary to INI format.
            
            Keys with dots are split into section and key parts.
            Keys without dots go into the DEFAULT section.
            
            :param data: Dictionary of configuration key-value pairs.
            
            :returns: The INI format configuration string.
            
            :raises ConfigurationError: If serialization fails.
        """
        # No interpolation, as in load(): a "%" in a value is written as it is.
        parser = configparser.ConfigParser(interpolation=None)
        
        # Group keys by section
        sections: Dict[str, Dict[str, str]] = {}
        defaults: Dict[str, str] = {}
        
        for key, value in data.items():
            if "." in key:
                # Split into section and key
                parts = key.split(".", 1)
                section = parts[0]
                subkey = parts[1]
                
                if section not in sections:
                    sections[section] = {}
                sections[section][subkey] = str(value)
            else:
                # Top-level key goes to defaults
                defaults[key] = str(value)
        
        # Set defaults
        for key, value in defaults.items():
            parser.set("DEFAULT", key, value)
        
        # Create sections
        for section, items in sections.items():
            parser.add_section(section)
            for key, value in items.items():
                parser.set(section, key, value)
        
        # Write to string
        import io
        output = io.StringIO()
        parser.write(output)
        return output.getvalue()


# Try to import yaml, but make it optional
try:
    import yaml
    YAML_AVAILABLE = True
except ImportError:
    YAML_AVAILABLE = False


def _flatten_dict(data: Dict[str, Any], prefix: str = "") -> Dict[str, Any]:
    """
        Flatten a nested dictionary into dot-notation keys.
        
        :param data: The nested dictionary to flatten.
        :param prefix: The current key prefix.
        
        :returns: A flattened dictionary with dot-notation keys.
    """
    result: Dict[str, Any] = {}
    
    for key, value in data.items():
        full_key = f"{prefix}.{key}" if prefix else key
        
        if isinstance(value, dict):
            # Recursively flatten nested dictionaries
            result.update(_flatten_dict(value, full_key))
        else:
            result[full_key] = value
    
    return result


def _unflatten_dict(data: Dict[str, Any]) -> Dict[str, Any]:
    """
        Unflatten a dot-notation dictionary into a nested dictionary.
        
        :param data: The flat dictionary with dot-notation keys.
        
        :returns: A nested dictionary.
    """
    result: Dict[str, Any] = {}
    
    for key, value in data.items():
        parts = key.split(".")
        current = result
        
        for i, part in enumerate(parts[:-1]):
            if part not in current:
                current[part] = {}
            elif not isinstance(current[part], dict):
                # Handle case where a key is both a value and a parent
                current[part] = {"": current[part]}
            current = current[part]
        
        current[parts[-1]] = value
    
    return result


class YamlLoader(ConfigLoader):
    """
        Configuration loader for YAML format files.
        
        This loader parses YAML format configuration files using the PyYAML
        library. Nested structures are flattened to dot-notation keys.
        
        Example YAML content::
        
            database:
              host: localhost
              port: 5432
            logging:
              level: DEBUG
        
        Results in::
        
            {
                "database.host": "localhost",
                "database.port": 5432,
                "logging.level": "DEBUG"
            }
        
        Note: PyYAML must be installed to use this loader.
    """
    
    def __init__(self):
        """
            Initialize the YamlLoader.
            
            :raises ConfigurationError: If PyYAML is not installed.
        """
        if not YAML_AVAILABLE:
            raise ConfigurationError(
                "PyYAML is not installed. Install it with: pip install pyyaml"
            )
    
    def load(self, content: str) -> Dict[str, Any]:
        """
            Parse YAML format content and return a dictionary.
            
            Nested structures are flattened to dot-notation keys.
            
            :param content: The YAML format content string to parse.
            
            :returns: Dictionary of configuration key-value pairs.
            
            :raises ConfigurationError: If parsing fails.
        """
        try:
            data = yaml.safe_load(content)
        except yaml.YAMLError as e:
            logger.warning("YAML loader: parse failure: %s", e)
            raise ConfigurationError(f"Failed to parse YAML content: {e}") from e
        
        if data is None:
            return {}
        
        if not isinstance(data, dict):
            raise ConfigurationError(
                f"YAML content must be a mapping, got {type(data).__name__}"
            )
        
        return _flatten_dict(data)
    
    def dump(self, data: Dict[str, Any]) -> str:
        """
            Serialize configuration dictionary to YAML format.
            
            Dot-notation keys are unflattened to nested structures.
            
            :param data: Dictionary of configuration key-value pairs.
            
            :returns: The YAML format configuration string.
            
            :raises ConfigurationError: If serialization fails.
        """
        try:
            nested = _unflatten_dict(data)
            return yaml.safe_dump(nested, default_flow_style=False)
        except yaml.YAMLError as e:
            logger.warning("YAML loader: serialization failure: %s", e)
            raise ConfigurationError(f"Failed to serialize to YAML: {e}") from e


class JsonLoader(ConfigLoader):
    """
        Configuration loader for JSON format files.
        
        This loader parses JSON format configuration files using Python's
        built-in json module. Nested structures are flattened to dot-notation keys.
        
        Example JSON content::
        
            {
                "database": {
                    "host": "localhost",
                    "port": 5432
                },
                "logging": {
                    "level": "DEBUG"
                }
            }
        
        Results in::
        
            {
                "database.host": "localhost",
                "database.port": 5432,
                "logging.level": "DEBUG"
            }
    """
    
    def load(self, content: str) -> Dict[str, Any]:
        """
            Parse JSON format content and return a dictionary.
            
            Nested structures are flattened to dot-notation keys.
            
            :param content: The JSON format content string to parse.
            
            :returns: Dictionary of configuration key-value pairs.
            
            :raises ConfigurationError: If parsing fails.
        """
        try:
            data = json.loads(content)
        except json.JSONDecodeError as e:
            logger.warning("JSON loader: parse failure: %s", e)
            raise ConfigurationError(f"Failed to parse JSON content: {e}") from e
        
        if not isinstance(data, dict):
            raise ConfigurationError(
                f"JSON content must be an object, got {type(data).__name__}"
            )
        
        return _flatten_dict(data)
    
    def dump(self, data: Dict[str, Any]) -> str:
        """
            Serialize configuration dictionary to JSON format.
            
            Dot-notation keys are unflattened to nested structures.
            
            :param data: Dictionary of configuration key-value pairs.
            
            :returns: The JSON format configuration string.
            
            :raises ConfigurationError: If serialization fails.
        """
        try:
            nested = _unflatten_dict(data)
            return json.dumps(nested, indent=2)
        except (TypeError, ValueError) as e:
            logger.warning("JSON loader: serialization failure: %s", e)
            raise ConfigurationError(f"Failed to serialize to JSON: {e}") from e


# Try to import tomllib (Python 3.11+) or tomli as fallback
try:
    import tomllib
    TOML_AVAILABLE = True
    TOML_MODULE = "tomllib"
except ImportError:
    try:
        import tomli as tomllib
        TOML_AVAILABLE = True
        TOML_MODULE = "tomli"
    except ImportError:
        TOML_AVAILABLE = False
        TOML_MODULE = None

# Try to import tomli_w for writing TOML
try:
    import tomli_w
    TOML_WRITE_AVAILABLE = True
except ImportError:
    TOML_WRITE_AVAILABLE = False


class TomlLoader(ConfigLoader):
    """
        Configuration loader for TOML format files.
        
        This loader parses TOML format configuration files using Python's
        tomllib module (Python 3.11+) or the tomli package as a fallback.
        Nested structures are flattened to dot-notation keys.
        
        Example TOML content::
        
            [database]
            host = "localhost"
            port = 5432
            
            [logging]
            level = "DEBUG"
        
        Results in::
        
            {
                "database.host": "localhost",
                "database.port": 5432,
                "logging.level": "DEBUG"
            }
        
        Note: For Python < 3.11, the tomli package must be installed.
              For writing TOML, the tomli_w package must be installed.
    """
    
    def __init__(self):
        """
            Initialize the TomlLoader.
            
            :raises ConfigurationError: If TOML parsing library is not available.
        """
        if not TOML_AVAILABLE:
            raise ConfigurationError(
                "TOML parsing library not available. "
                "For Python < 3.11, install tomli with: pip install tomli"
            )
    
    def load(self, content: str) -> Dict[str, Any]:
        """
            Parse TOML format content and return a dictionary.
            
            Nested structures are flattened to dot-notation keys.
            
            :param content: The TOML format content string to parse.
            
            :returns: Dictionary of configuration key-value pairs.
            
            :raises ConfigurationError: If parsing fails.
        """
        try:
            # tomllib.loads expects bytes in Python 3.11+
            if TOML_MODULE == "tomllib":
                data = tomllib.loads(content)
            else:
                data = tomllib.loads(content)
        except Exception as e:
            logger.warning("TOML loader: parse failure: %s", e)
            raise ConfigurationError(f"Failed to parse TOML content: {e}") from e
        
        return _flatten_dict(data)
    
    def dump(self, data: Dict[str, Any]) -> str:
        """
            Serialize configuration dictionary to TOML format.
            
            Dot-notation keys are unflattened to nested structures.
            
            :param data: Dictionary of configuration key-value pairs.
            
            :returns: The TOML format configuration string.
            
            :raises ConfigurationError: If serialization fails or tomli_w not installed.
        """
        if not TOML_WRITE_AVAILABLE:
            raise ConfigurationError(
                "TOML writing not available. Install tomli_w with: pip install tomli_w"
            )
        
        try:
            nested = _unflatten_dict(data)
            return tomli_w.dumps(nested)
        except Exception as e:
            logger.warning("TOML loader: serialization failure: %s", e)
            raise ConfigurationError(f"Failed to serialize to TOML: {e}") from e


# Mapping of file extensions to loader classes
FORMAT_LOADERS: Dict[str, type] = {
    "ini": IniLoader,
    "cfg": IniLoader,
    "conf": IniLoader,
    "json": JsonLoader,
}

# Add YAML loader if available
if YAML_AVAILABLE:
    FORMAT_LOADERS["yaml"] = YamlLoader
    FORMAT_LOADERS["yml"] = YamlLoader

# Add TOML loader if available
if TOML_AVAILABLE:
    FORMAT_LOADERS["toml"] = TomlLoader


# Include directive patterns for different formats. A pattern matches one
# line: the path may be quoted, never runs past the end of the line, and
# is the first group.
INCLUDE_PATTERNS = {
    "ini": r'^[ \t]*%include[ \t]+["\']?([^"\'\r\n]+?)["\']?[ \t]*$',
    "yaml": r'^[ \t]*#[ \t]*!include[ \t]+["\']?([^"\'\r\n]+?)["\']?[ \t]*$',
    "json": None,  # JSON doesn't support comments, so no include directive
    "toml": r'^[ \t]*#[ \t]*!include[ \t]+["\']?([^"\'\r\n]+?)["\']?[ \t]*$',
}

# File formats that are written like another one and share its include
# directive.
INCLUDE_FORMAT_ALIASES = {
    "yml": "yaml",
    "cfg": "ini",
    "conf": "ini",
}

# The characters that start a comment line in each format, used to tell
# whether an include directive comes before a file's own settings.
INCLUDE_COMMENT_PREFIXES = {
    "ini": ("#", ";"),
    "yaml": ("#",),
    "toml": ("#",),
}


class FileSource(ConfigSource):
    """
        Configuration source that reads from files.
        
        This source loads configuration values from one or more files,
        supporting multiple formats (INI, YAML, JSON, TOML). Files are
        loaded in the order specified, with later files taking precedence.
        
        The file format can be explicitly specified or auto-detected from
        the file extension.
        
        Example usage::
        
            # Auto-detect format from extension
            source = FileSource(paths=[Path("config.yaml")])
            
            # Explicit format
            source = FileSource(paths=[Path("config")], format="yaml")
            
            # Multiple files with precedence
            source = FileSource(paths=[
                Path("defaults.yaml"),
                Path("local.yaml")
            ])
        
        A file can include other files with a directive on a line of its
        own: ``# !include other.yaml`` in YAML and TOML files and
        ``%include other.ini`` in INI files (``.yml``, ``.cfg`` and
        ``.conf`` files use the directive of their format). The path may
        be quoted and is relative to the including file. An included file
        is parsed by itself, in the format its extension names, and its
        settings are merged key by key with those of the including file:
        an include placed before the file's own settings is overridden by
        them, and an include placed after any of them overrides them. A
        file may be included from several places; a file that includes
        itself, directly or through others, is an error.
        
        :param paths: List of file paths to load (in precedence order, later wins).
        :param format: File format (auto-detected from extension if not provided).
        :param required: Whether files must exist (default: False).
        :param process_includes: Whether to process include directives (default: True).
    """
    
    def __init__(
        self,
        paths: List[Union[str, Path]],
        format: Optional[str] = None,
        required: bool = False,
        process_includes: bool = True
    ):
        """
            Initialize the FileSource.
            
            :param paths: List of file paths to load.
            :param format: File format (auto-detected if not provided).
            :param required: Whether files must exist.
            :param process_includes: Whether to process include directives.
        """
        self._paths = [Path(p) if isinstance(p, str) else p for p in paths]
        self._format = format
        self._required = required
        self._process_includes = process_includes
        self._loaders: Dict[str, ConfigLoader] = {}
    
    @property
    def paths(self) -> List[Path]:
        """
            Get the list of file paths.
            
            :returns: List of Path objects.
        """
        return self._paths
    
    @property
    def format(self) -> Optional[str]:
        """
            Get the explicit format setting.
            
            :returns: The format string or None if auto-detecting.
        """
        return self._format
    
    @property
    def required(self) -> bool:
        """
            Get whether files are required to exist.
            
            :returns: True if files must exist, False otherwise.
        """
        return self._required
    
    @property
    def source_type(self) -> ConfigSourceType:
        """
            Return the source type for precedence ordering.
            
            :returns: ConfigSourceType.FILE
        """
        return ConfigSourceType.FILE
    
    def _get_format(self, path: Path) -> str:
        """
            Get the format for a file path.
            
            If an explicit format was set, use that. Otherwise, detect
            from the file extension.
            
            :param path: The file path.
            
            :returns: The format string (e.g., "yaml", "json").
            
            :raises ConfigurationError: If format cannot be determined.
        """
        if self._format:
            return self._format
        
        # Get extension without the dot
        ext = path.suffix.lstrip(".").lower()
        
        if not ext:
            raise ConfigurationError(
                f"Cannot determine format for file without extension: {path}"
            )
        
        if ext not in FORMAT_LOADERS:
            raise ConfigurationError(
                f"Unsupported file format '{ext}' for file: {path}"
            )
        
        return ext
    
    def _get_loader(self, format: str) -> ConfigLoader:
        """
            Get or create a loader for the specified format.
            
            :param format: The format string.
            
            :returns: A ConfigLoader instance.
            
            :raises ConfigurationError: If format is not supported.
        """
        if format not in self._loaders:
            if format not in FORMAT_LOADERS:
                raise ConfigurationError(f"Unsupported format: {format}")
            self._loaders[format] = FORMAT_LOADERS[format]()
        
        return self._loaders[format]
    
    def _split_include_directives(
        self,
        content: str,
        format: str
    ) -> Tuple[List[str], List[str], str]:
        """
            Take the include directives out of configuration content.
            
            :param content: The configuration content.
            :param format: The file format.
            
            :returns: ``(leading, trailing, own_content)``: the paths of the
                      directives that come before the first setting of the
                      content, the paths of the directives that come after
                      it, and the content with every directive line emptied
                      (so line numbers in parse errors stay right).
        """
        leading: List[str] = []
        trailing: List[str] = []
        
        directive_format = INCLUDE_FORMAT_ALIASES.get(format, format)
        
        # Get the include pattern for this format
        pattern_str = INCLUDE_PATTERNS.get(directive_format)
        if pattern_str is None:
            return leading, trailing, content
        
        pattern = re.compile(pattern_str)
        comment_prefixes = INCLUDE_COMMENT_PREFIXES.get(directive_format, ("#",))
        
        own_lines: List[str] = []
        settings_started = False
        
        for line in content.split("\n"):
            match = pattern.match(line)
            if match is not None:
                include_path_str = match.group(1).strip()
                if settings_started:
                    trailing.append(include_path_str)
                else:
                    leading.append(include_path_str)
                own_lines.append("")
                continue
            
            stripped = line.strip()
            if stripped != "" and not stripped.startswith(comment_prefixes):
                settings_started = True
            
            own_lines.append(line)
        
        own_content = "\n".join(own_lines)
        return leading, trailing, own_content
    
    def _load_included_file(
        self,
        include_path_str: str,
        including_path: Path,
        including_format: str,
        include_stack: List[Path]
    ) -> Dict[str, Any]:
        """
            Load a file named by an include directive.
            
            :param include_path_str: The path as written in the directive.
            :param including_path: The file the directive is in.
            :param including_format: The format of the including file, used
                                     for an included file whose extension
                                     does not name a format.
            :param include_stack: The files being loaded, outermost first.
            
            :returns: Dictionary of configuration key-value pairs.
            
            :raises ConfigurationFileNotFoundError: If included file not found.
            :raises ConfigurationError: If circular include detected.
        """
        # Resolve relative path
        if not os.path.isabs(include_path_str):
            include_path = including_path.parent / include_path_str
        else:
            include_path = Path(include_path_str)
        
        include_path = include_path.resolve()
        
        # Check for circular includes: only a file that is still being
        # loaded further up counts. Two files that both include a third
        # are not a cycle.
        if include_path in include_stack:
            chain = [str(stacked) for stacked in include_stack]
            chain.append(str(include_path))
            raise ConfigurationError(
                f"Circular include detected: {' -> '.join(chain)}"
            )
        
        # Check if file exists
        if not include_path.exists():
            raise ConfigurationFileNotFoundError(
                include_path,
                referenced_from=including_path
            )
        
        # The included file is read in its own format when its extension
        # names one, and in the including file's format otherwise.
        include_format = self._format
        if not include_format:
            include_format = include_path.suffix.lstrip(".").lower()
            if include_format not in FORMAT_LOADERS:
                include_format = including_format
        
        return self._load_file_content(include_path, include_format, include_stack)
    
    def _load_file_content(
        self,
        path: Path,
        format: str,
        include_stack: List[Path]
    ) -> Dict[str, Any]:
        """
            Read and parse one file, merging in the files it includes.
            
            The file's own settings are parsed as a whole. The files named
            by include directives are loaded separately and merged key by
            key: those included before the first setting are overridden by
            the file's own settings, and those included after it override
            them.
            
            :param path: The file path.
            :param format: The format to read the file in.
            :param include_stack: The files being loaded, outermost first.
            
            :returns: Dictionary of configuration key-value pairs.
        """
        loader = self._get_loader(format)
        
        # Read file content
        content = path.read_text()
        
        if not self._process_includes:
            return loader.load(content)
        
        leading, trailing, own_content = self._split_include_directives(content, format)
        
        result: Dict[str, Any] = {}
        
        include_stack.append(path.resolve())
        try:
            for include_path_str in leading:
                included = self._load_included_file(include_path_str, path, format, include_stack)
                result.update(included)
            
            # Parse content
            own_settings = loader.load(own_content)
            result.update(own_settings)
            
            for include_path_str in trailing:
                included = self._load_included_file(include_path_str, path, format, include_stack)
                result.update(included)
        finally:
            include_stack.pop()
        
        return result
    
    def _load_file(
        self,
        path: Path,
        visited: Optional[set] = None
    ) -> Dict[str, Any]:
        """
            Load configuration from a single file.
            
            :param path: The file path.
            :param visited: Files that are already being loaded and so may
                            not be included again (for include processing).
            
            :returns: Dictionary of configuration key-value pairs.
            
            :raises ConfigurationFileNotFoundError: If file not found and required.
            :raises ConfigurationError: If loading fails.
        """
        if not path.exists():
            if self._required:
                raise ConfigurationFileNotFoundError(path)
            return {}
        
        # Get format
        format = self._get_format(path)
        
        include_stack: List[Path] = []
        if visited is not None:
            include_stack.extend(visited)
        
        return self._load_file_content(path, format, include_stack)
    
    def load(self) -> Dict[str, Any]:
        """
            Load configuration from all files.
            
            Files are loaded in order, with later files taking precedence
            over earlier ones for the same keys.
            
            :returns: Dictionary of configuration key-value pairs.
            
            :raises ConfigurationFileNotFoundError: If required file not found.
            :raises ConfigurationError: If loading fails.
        """
        result: Dict[str, Any] = {}
        
        for path in self._paths:
            file_config = self._load_file(path)
            result.update(file_config)
        
        return result



# =============================================================================
# SecretsProvider Implementation
# =============================================================================

class SecretsProvider(ConfigSource):
    """
        Configuration source for sensitive values with security features.
        
        This source loads secrets from environment variables and/or encrypted
        files, providing secure handling of sensitive configuration values.
        It supports:
        
        - Loading secrets from environment variables with a configurable prefix
        - Loading secrets from encrypted files
        - Audit logging for secret access
        - Secret rotation via reload()
        
        All secrets are wrapped in SecretValue instances to prevent accidental
        exposure in logs, error messages, or string representations.
        
        A secrets file is encrypted and authenticated with AES-256-GCM under
        a key derived from ``encryption_key`` with PBKDF2. It starts with a
        header naming the format version, and the header is authenticated
        with the content, so a file that was changed in any way, or that was
        encrypted with another key, is refused. Files written by releases
        up to 1.6.0 have no header and are encrypted with AES-CBC, which
        does not detect changes; they are refused unless
        ``allow_legacy_secrets_format`` is set, which is meant for reading
        such a file once in order to write it again in the current format.
        
        A ``secrets_file`` that does not exist is an error, so a mistyped or
        unmounted path cannot leave the application running without its
        secrets. Pass ``secrets_file_required=False`` for a file that is
        allowed to be absent.
        
        Example usage::
        
            # Load secrets from environment variables
            provider = SecretsProvider(env_prefix="SECRET_")
            
            # Load secrets from encrypted file
            provider = SecretsProvider(
                secrets_file=Path("secrets.enc"),
                encryption_key=b"my-32-byte-encryption-key-here!"
            )
            
            # With audit logging
            def audit_log(key: str):
                print(f"Secret accessed: {key}")
            
            provider = SecretsProvider(
                env_prefix="SECRET_",
                audit_logger=audit_log
            )
        
        :param env_prefix: Prefix for secret environment variables (e.g., "SECRET_").
        :param secrets_file: Optional path to encrypted secrets file.
        :param encryption_key: Key for encrypting/decrypting secrets file (32 bytes for AES-256).
        :param audit_logger: Optional callable for logging secret access events.
        :param secrets_file_required: Whether a configured secrets file must exist (default: True).
        :param allow_legacy_secrets_format: Whether to read a secrets file in the
                                            unauthenticated format of releases up to 1.6.0
                                            (default: False).
    """
    
    # AES block size for encryption (legacy AES-CBC format only)
    AES_BLOCK_SIZE = 16
    
    # Salt size for key derivation
    SALT_SIZE = 16
    
    # Nonce size for AES-GCM
    NONCE_SIZE = 12
    
    # Authentication tag size of AES-GCM
    TAG_SIZE = 16
    
    # Number of iterations for key derivation
    KDF_ITERATIONS = 600000
    
    # Number of iterations used by the legacy AES-CBC format
    LEGACY_KDF_ITERATIONS = 100000
    
    # The first bytes of an encrypted secrets file, followed by one byte
    # holding the format version
    FORMAT_MAGIC = b"WWSECRETS"
    
    # Format version 2: AES-256-GCM, PBKDF2-HMAC-SHA256 with KDF_ITERATIONS
    FORMAT_VERSION = 2
    
    def __init__(
        self,
        env_prefix: str = "SECRET_",
        secrets_file: Optional[Path] = None,
        encryption_key: Optional[bytes] = None,
        audit_logger: Optional[Callable[[str], None]] = None,
        secrets_file_required: bool = True,
        allow_legacy_secrets_format: bool = False
    ):
        """
            Initialize the SecretsProvider.
            
            :param env_prefix: Prefix for secret environment variables.
            :param secrets_file: Path to encrypted secrets file.
            :param encryption_key: Key for decrypting secrets file.
            :param audit_logger: Optional logger for audit trail.
            :param secrets_file_required: Whether ``secrets_file`` must exist.
                                          When False, a missing file is skipped.
            :param allow_legacy_secrets_format: Whether to read a secrets file
                                                written in the unauthenticated
                                                AES-CBC format of releases up
                                                to 1.6.0.
        """
        self._env_prefix = env_prefix
        self._secrets_file = Path(secrets_file) if secrets_file else None
        self._encryption_key = encryption_key
        self._audit_logger = audit_logger
        self._secrets_file_required = secrets_file_required
        self._allow_legacy_secrets_format = allow_legacy_secrets_format
        self._secrets: Dict[str, 'SecretValue'] = {}
        self._loaded = False
        self._known_keys: Dict[str, Optional[str]] = {}
    
    def use_known_keys(self, keys: List[str]) -> None:
        """
            Remember the keys the schema defines, so a variable name is
            mapped to the schema key it spells (SECRET_API_KEY to
            ``api_key`` when the schema defines that key).
            
            :param keys: The keys defined by the registry's schema.
        """
        self._known_keys = _build_known_key_lookup(keys, "_", True)
        return
    
    @property
    def env_prefix(self) -> str:
        """
            Get the environment variable prefix for secrets.
            
            :returns: The prefix string.
        """
        return self._env_prefix
    
    @property
    def secrets_file(self) -> Optional[Path]:
        """
            Get the path to the secrets file.
            
            :returns: The Path object or None if not configured.
        """
        return self._secrets_file
    
    @property
    def source_type(self) -> ConfigSourceType:
        """
            Return the source type for precedence ordering.
            
            :returns: ConfigSourceType.SECRETS
        """
        return ConfigSourceType.SECRETS
    
    def _transform_env_name(self, env_name: str) -> str:
        """
            Transform an environment variable name to a configuration key.
            
            This method removes the prefix, replaces underscores with dots,
            and lowercases the result. A doubled underscore marks the
            nesting levels explicitly, and a name that spells a key of the
            schema is mapped to that key; see
            :func:`_environment_name_to_key`.
            
            :param env_name: The environment variable name.
            
            :returns: The transformed configuration key.
        """
        # Remove the prefix
        name = env_name[len(self._env_prefix):]
        
        key = _environment_name_to_key(name, "_", True, self._known_keys)
        return key
    
    def _load_from_environment(self) -> Dict[str, str]:
        """
            Load secrets from environment variables.
            
            :returns: Dictionary of secret key-value pairs.
        """
        result: Dict[str, str] = {}
        
        for env_name, env_value in os.environ.items():
            if not env_name.startswith(self._env_prefix):
                continue
            
            config_key = self._transform_env_name(env_name)
            result[config_key] = env_value
        
        return result
    
    def _load_from_file(self) -> Dict[str, str]:
        """
            Load secrets from encrypted file.
            
            :returns: Dictionary of secret key-value pairs.
            
            :raises ConfigurationFileNotFoundError: If secrets file not found.
            :raises ConfigurationError: If decryption fails.
        """
        if self._secrets_file is None:
            return {}
        
        if not self._secrets_file.exists():
            raise ConfigurationFileNotFoundError(self._secrets_file)
        
        if self._encryption_key is None:
            raise ConfigurationError(
                "Encryption key required to read encrypted secrets file"
            )
        
        # Read encrypted content
        encrypted_content = self._secrets_file.read_bytes()
        
        # Decrypt
        decrypted_content = self.decrypt_secrets(encrypted_content)
        
        # Parse JSON
        try:
            return json.loads(decrypted_content)
        except json.JSONDecodeError as e:
            logger.warning(
                "SecretsProvider: decrypted secrets payload is not valid JSON: %s", e
            )
            raise ConfigurationError(f"Failed to parse secrets file: {e}") from e
    
    def load(self) -> Dict[str, Any]:
        """
            Load secrets from configured sources.
            
            Secrets are loaded from environment variables first, then from
            the encrypted file (if configured). File secrets take precedence
            over environment secrets for the same key.
            
            All values are wrapped in SecretValue instances.
            
            :returns: Dictionary of configuration key to SecretValue pairs.
            
            :raises ConfigurationFileNotFoundError: If a secrets file is
                configured, required and does not exist.
            :raises ConfigurationError: If loading fails.
        """
        # Load from environment
        secrets = self._load_from_environment()
        
        # Load from file (overrides environment). A configured file that is
        # missing is an error unless it was declared optional.
        if self._secrets_file is not None:
            if self._secrets_file_required or self._secrets_file.exists():
                file_secrets = self._load_from_file()
                secrets.update(file_secrets)
        
        # Wrap all values in SecretValue
        self._secrets = {}
        result: Dict[str, Any] = {}
        
        for key, value in secrets.items():
            secret_value = SecretValue(
                value=str(value),
                key=key,
                audit_logger=self._audit_logger
            )
            self._secrets[key] = secret_value
            result[key] = secret_value
        
        self._loaded = True
        return result
    
    def get_secret(self, key: str) -> Optional['SecretValue']:
        """
            Get a secret value by key.
            
            :param key: The secret key.
            
            :returns: SecretValue wrapper or None if not found.
        """
        if not self._loaded:
            self.load()
        
        return self._secrets.get(key)
    
    def reload(self) -> Dict[str, Any]:
        """
            Reload secrets from sources.
            
            This method allows reloading secrets without restarting the
            application, supporting secret rotation scenarios.
            
            :returns: Dictionary of configuration key to SecretValue pairs.
        """
        self._secrets.clear()
        self._loaded = False
        return self.load()
    
    def encrypt_secrets(self, secrets_data: Dict[str, str]) -> bytes:
        """
            Encrypt secrets data for writing to file.
            
            Uses AES-256-GCM, which authenticates the data as well as
            encrypting it, with a key derived by PBKDF2-HMAC-SHA256. The
            result is::
            
                FORMAT_MAGIC | version (1 byte) | salt | nonce | ciphertext and tag
            
            The magic, version and salt are authenticated together with the
            ciphertext.
            
            :param secrets_data: Dictionary of secret key-value pairs.
            
            :returns: Encrypted bytes.
            
            :raises ConfigurationError: If encryption fails or key not provided.
        """
        if self._encryption_key is None:
            raise ConfigurationError(
                "Encryption key required to encrypt secrets"
            )
        
        try:
            from cryptography.hazmat.primitives.ciphers.aead import AESGCM
        except ImportError:
            raise ConfigurationError(
                "cryptography package required for secrets encryption. "
                "Install with: pip install cryptography"
            )
        
        # Convert to JSON
        plaintext = json.dumps(secrets_data).encode('utf-8')
        
        # Generate random salt for key derivation and a random nonce
        salt = os.urandom(self.SALT_SIZE)
        nonce = os.urandom(self.NONCE_SIZE)
        
        # Derive key using PBKDF2
        derived_key = self._derive_key(self._encryption_key, salt)
        
        header = self.FORMAT_MAGIC + bytes([self.FORMAT_VERSION])
        authenticated_data = header + salt
        
        # Encrypt and authenticate
        cipher = AESGCM(derived_key)
        ciphertext = cipher.encrypt(nonce, plaintext, authenticated_data)
        
        # Return header + salt + nonce + ciphertext (which ends with the tag)
        return header + salt + nonce + ciphertext
    
    def decrypt_secrets(self, encrypted_data: bytes) -> str:
        """
            Decrypt secrets data from file.
            
            Data in the current format is authenticated: decryption fails
            when a single bit of it was changed or the key is not the one it
            was encrypted with. Data without the format header is in the
            unauthenticated AES-CBC format of releases up to 1.6.0 and is
            refused unless the provider was created with
            ``allow_legacy_secrets_format=True``.
            
            :param encrypted_data: Encrypted bytes, as returned by :meth:`encrypt_secrets`.
            
            :returns: Decrypted JSON string.
            
            :raises ConfigurationError: If decryption fails.
        """
        if self._encryption_key is None:
            raise ConfigurationError(
                "Encryption key required to decrypt secrets"
            )
        
        if not encrypted_data.startswith(self.FORMAT_MAGIC):
            if not self._allow_legacy_secrets_format:
                errmsg_lines = [
                    "The secrets data is not in the authenticated format written by this release.",
                    "A secrets file written by release 1.6.0 or earlier is encrypted without authentication,",
                    "so changes made to it cannot be detected, and it is not read by default.",
                    "To convert such a file, load it once with SecretsProvider(allow_legacy_secrets_format=True)",
                    "and write it again with write_encrypted_secrets().",
                ]
                errmsg = os.linesep.join(errmsg_lines)
                raise ConfigurationError(errmsg)
            
            logger.warning(
                "SecretsProvider: reading secrets in the legacy unauthenticated format; "
                "write the file again with write_encrypted_secrets() to convert it"
            )
            return self._decrypt_legacy_secrets(encrypted_data)
        
        try:
            from cryptography.exceptions import InvalidTag
            from cryptography.hazmat.primitives.ciphers.aead import AESGCM
        except ImportError:
            raise ConfigurationError(
                "cryptography package required for secrets decryption. "
                "Install with: pip install cryptography"
            )
        
        header_size = len(self.FORMAT_MAGIC) + 1
        
        # Validate minimum length
        min_length = header_size + self.SALT_SIZE + self.NONCE_SIZE + self.TAG_SIZE
        if len(encrypted_data) < min_length:
            raise ConfigurationError("Invalid encrypted data: too short")
        
        version = encrypted_data[len(self.FORMAT_MAGIC)]
        if version != self.FORMAT_VERSION:
            raise ConfigurationError(
                f"Unsupported secrets format version {version}; this release reads version {self.FORMAT_VERSION}"
            )
        
        # Extract header, salt, nonce, and ciphertext
        salt_end = header_size + self.SALT_SIZE
        nonce_end = salt_end + self.NONCE_SIZE
        
        header = encrypted_data[:header_size]
        salt = encrypted_data[header_size:salt_end]
        nonce = encrypted_data[salt_end:nonce_end]
        ciphertext = encrypted_data[nonce_end:]
        
        # Derive key using PBKDF2
        derived_key = self._derive_key(self._encryption_key, salt)
        
        authenticated_data = header + salt
        
        # Decrypt and verify
        try:
            cipher = AESGCM(derived_key)
            plaintext = cipher.decrypt(nonce, ciphertext, authenticated_data)
        except InvalidTag as e:
            logger.warning(
                "SecretsProvider: decryption failed (authentication); raising ConfigurationError"
            )
            raise ConfigurationError(
                "Failed to decrypt secrets: the data was modified or the encryption key is wrong"
            ) from e
        
        try:
            return plaintext.decode('utf-8')
        except UnicodeDecodeError as e:
            raise ConfigurationError(f"Failed to decrypt secrets: {e}") from e
    
    def _decrypt_legacy_secrets(self, encrypted_data: bytes) -> str:
        """
            Decrypt secrets data in the format of releases up to 1.6.0:
            salt + iv + AES-256-CBC ciphertext, without authentication.
            
            :param encrypted_data: Encrypted bytes (salt + iv + ciphertext).
            
            :returns: Decrypted JSON string.
            
            :raises ConfigurationError: If decryption fails.
        """
        try:
            from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
            from cryptography.hazmat.primitives import padding
            from cryptography.hazmat.backends import default_backend
        except ImportError:
            raise ConfigurationError(
                "cryptography package required for secrets decryption. "
                "Install with: pip install cryptography"
            )
        
        # Validate minimum length
        min_length = self.SALT_SIZE + self.AES_BLOCK_SIZE + self.AES_BLOCK_SIZE
        if len(encrypted_data) < min_length:
            raise ConfigurationError("Invalid encrypted data: too short")
        
        # Extract salt, iv, and ciphertext
        salt = encrypted_data[:self.SALT_SIZE]
        iv = encrypted_data[self.SALT_SIZE:self.SALT_SIZE + self.AES_BLOCK_SIZE]
        ciphertext = encrypted_data[self.SALT_SIZE + self.AES_BLOCK_SIZE:]
        
        # Derive key using PBKDF2
        derived_key = self._derive_key(self._encryption_key, salt, iterations=self.LEGACY_KDF_ITERATIONS)
        
        # Decrypt
        try:
            cipher = Cipher(
                algorithms.AES(derived_key),
                modes.CBC(iv),
                backend=default_backend()
            )
            decryptor = cipher.decryptor()
            padded_data = decryptor.update(ciphertext) + decryptor.finalize()
            
            # Unpad
            unpadder = padding.PKCS7(self.AES_BLOCK_SIZE * 8).unpadder()
            plaintext = unpadder.update(padded_data) + unpadder.finalize()
            
            return plaintext.decode('utf-8')
        except Exception as e:
            logger.warning(
                "SecretsProvider: decryption failed (%s); raising ConfigurationError",
                type(e).__name__,
            )
            raise ConfigurationError(f"Failed to decrypt secrets: {e}") from e
    
    def _derive_key(self, password: bytes, salt: bytes, iterations: Optional[int] = None) -> bytes:
        """
            Derive an encryption key from password using PBKDF2.
            
            :param password: The password/key bytes.
            :param salt: Random salt bytes.
            :param iterations: Number of PBKDF2 iterations. Defaults to KDF_ITERATIONS.
            
            :returns: 32-byte derived key for AES-256.
        """
        try:
            from cryptography.hazmat.primitives import hashes
            from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
            from cryptography.hazmat.backends import default_backend
        except ImportError:
            raise ConfigurationError(
                "cryptography package required for key derivation. "
                "Install with: pip install cryptography"
            )
        
        if iterations is None:
            iterations = self.KDF_ITERATIONS
        
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,  # 256 bits for AES-256
            salt=salt,
            iterations=iterations,
            backend=default_backend()
        )
        
        return kdf.derive(password)
    
    def write_encrypted_secrets(
        self,
        secrets_data: Dict[str, str],
        output_path: Optional[Path] = None
    ) -> None:
        """
            Write secrets to an encrypted file.
            
            :param secrets_data: Dictionary of secret key-value pairs.
            :param output_path: Path to write to (uses secrets_file if not provided).
            
            :raises ConfigurationError: If encryption fails or no path specified.
        """
        path = output_path or self._secrets_file
        if path is None:
            raise ConfigurationError(
                "No output path specified for encrypted secrets"
            )
        
        encrypted = self.encrypt_secrets(secrets_data)
        path.write_bytes(encrypted)


# =============================================================================
# Configuration File Discovery
# =============================================================================

import fnmatch


# Default search directories for configuration files
DEFAULT_SEARCH_DIRECTORIES: List[str] = [
    ".",                    # Current directory
    "./config",             # Config subdirectory
    "~/.config/{appname}",  # User config directory
    "/etc/{appname}",       # System config directory
]

# Default file name patterns
DEFAULT_FILE_PATTERNS: List[str] = [
    "settings.*",
    "config.*",
    "{appname}.*",
    "{appname}.config.*",
]


class ConfigFileDiscovery:
    """
        Configuration file discovery utility.
        
        This class provides automatic discovery of configuration files in
        configurable directories, supporting file name patterns, environment-
        specific files, and profile-based configuration.
        
        File discovery follows these rules:
        
        1. Search directories are checked in order, and the files of a
           directory in the order of their names, so the result does not
           depend on the order the file system lists them in
        2. A base file is one whose name is a configured pattern with only
           the extension filled in: ``settings.yaml`` for ``settings.*``
        3. Environment-specific files (e.g., settings.production.yaml) are
           discovered when that environment is specified
        4. Profile-specific files are discovered when that profile is active
        
        A file qualified with any other name, such as ``settings.dev.yaml``
        while the profile is ``production``, belongs to another environment
        or profile and is not discovered.
        
        Example usage::
        
            # Basic discovery
            discovery = ConfigFileDiscovery(appname="myapp")
            files = discovery.discover()
            
            # With environment
            discovery = ConfigFileDiscovery(
                appname="myapp",
                environment="production"
            )
            files = discovery.discover()
            
            # With profile from environment variable
            discovery = ConfigFileDiscovery(
                appname="myapp",
                profile_env_var="APP_PROFILE"
            )
            files = discovery.discover()
        
        :param appname: Application name for pattern substitution.
        :param search_directories: List of directories to search.
        :param file_patterns: List of file name patterns to match.
        :param environment: Environment name (e.g., "production", "development").
        :param profile: Configuration profile name.
        :param profile_env_var: Environment variable for profile selection.
        :param supported_formats: List of supported file extensions.
    """
    
    def __init__(
        self,
        appname: str = "app",
        search_directories: Optional[List[str]] = None,
        file_patterns: Optional[List[str]] = None,
        environment: Optional[str] = None,
        profile: Optional[str] = None,
        profile_env_var: str = "APP_PROFILE",
        supported_formats: Optional[List[str]] = None
    ):
        """
            Initialize the ConfigFileDiscovery.
            
            :param appname: Application name for pattern substitution.
            :param search_directories: List of directories to search.
            :param file_patterns: List of file name patterns to match.
            :param environment: Environment name (e.g., "production").
            :param profile: Configuration profile name.
            :param profile_env_var: Environment variable for profile selection.
            :param supported_formats: List of supported file extensions.
        """
        self._appname = appname
        self._search_directories = search_directories or list(DEFAULT_SEARCH_DIRECTORIES)
        self._file_patterns = file_patterns or list(DEFAULT_FILE_PATTERNS)
        self._environment = environment
        self._profile = profile
        self._profile_env_var = profile_env_var
        self._supported_formats = supported_formats or list(FORMAT_LOADERS.keys())
    
    @property
    def appname(self) -> str:
        """
            Get the application name.
            
            :returns: The application name string.
        """
        return self._appname
    
    @property
    def search_directories(self) -> List[str]:
        """
            Get the list of search directories.
            
            :returns: List of directory path strings.
        """
        return self._search_directories
    
    @property
    def file_patterns(self) -> List[str]:
        """
            Get the list of file name patterns.
            
            :returns: List of pattern strings.
        """
        return self._file_patterns
    
    @property
    def environment(self) -> Optional[str]:
        """
            Get the environment name.
            
            :returns: The environment name or None.
        """
        return self._environment
    
    @property
    def profile(self) -> Optional[str]:
        """
            Get the configuration profile.
            
            If not explicitly set, checks the profile environment variable.
            
            :returns: The profile name or None.
        """
        if self._profile is not None:
            return self._profile
        
        return os.environ.get(self._profile_env_var)
    
    @property
    def supported_formats(self) -> List[str]:
        """
            Get the list of supported file formats.
            
            :returns: List of format extension strings.
        """
        return self._supported_formats
    
    def _expand_path(self, path_template: str) -> Path:
        """
            Expand a path template with variable substitution.
            
            Supports the following substitutions:
            - {appname}: Application name
            - ~: User home directory
            
            :param path_template: The path template string.
            
            :returns: Expanded Path object.
        """
        # Substitute {appname}
        expanded = path_template.replace("{appname}", self._appname)
        
        # Expand ~ to user home
        expanded = os.path.expanduser(expanded)
        
        return Path(expanded)
    
    def _expand_pattern(self, pattern: str) -> str:
        """
            Expand a file pattern with variable substitution.
            
            :param pattern: The pattern string.
            
            :returns: Expanded pattern string.
        """
        return pattern.replace("{appname}", self._appname)
    
    def _matches_pattern(self, filename: str, pattern: str) -> bool:
        """
            Check if a filename matches a pattern.
            
            :param filename: The filename to check.
            :param pattern: The pattern to match against.
            
            :returns: True if the filename matches the pattern.
        """
        expanded_pattern = self._expand_pattern(pattern)
        return fnmatch.fnmatch(filename, expanded_pattern)
    
    def _matches_base(self, filename: str) -> bool:
        """
            Check if a filename is a base configuration file for one of the
            configured patterns.
            
            For a pattern that ends with ``.*`` the ``*`` stands for the
            extension alone: ``settings.*`` matches ``settings.yaml`` and
            not ``settings.dev.yaml``. Any other pattern is matched against
            the whole filename.
            
            :param filename: The filename to check.
            
            :returns: True if the filename is a base file of a pattern.
        """
        stem = Path(filename).stem
        
        for pattern in self._file_patterns:
            expanded_pattern = self._expand_pattern(pattern)
            
            if expanded_pattern.endswith(".*"):
                stem_pattern = expanded_pattern[:-2]
                if fnmatch.fnmatch(stem, stem_pattern):
                    return True
            elif fnmatch.fnmatch(filename, expanded_pattern):
                return True
        
        return False
    
    def _matches_overlay(self, filename: str, qualifier: str) -> bool:
        """
            Check if a filename is the overlay of a base file for an
            environment or profile name: ``settings.production.yaml`` is the
            ``production`` overlay of ``settings.yaml``.
            
            :param filename: The filename to check.
            :param qualifier: The environment or profile name.
            
            :returns: True if removing ``.<qualifier>`` from before the
                      extension gives the name of a base file.
        """
        path = Path(filename)
        stem = path.stem
        
        marker = f".{qualifier}".lower()
        if not stem.lower().endswith(marker):
            return False
        
        base_filename = stem[:len(stem) - len(marker)] + path.suffix
        return self._matches_base(base_filename)
    
    def _has_supported_format(self, filename: str) -> bool:
        """
            Check if a filename has a supported format extension.
            
            :param filename: The filename to check.
            
            :returns: True if the file has a supported extension.
        """
        ext = Path(filename).suffix.lstrip(".").lower()
        return ext in self._supported_formats
    
    def _get_base_name(self, filename: str) -> str:
        """
            Get the base name of a config file (without environment/profile suffix).
            
            For example:
            - "settings.yaml" -> "settings"
            - "settings.production.yaml" -> "settings"
            - "config.dev.json" -> "config"
            
            :param filename: The filename.
            
            :returns: The base name.
        """
        path = Path(filename)
        name = path.stem  # Remove extension
        
        # Check if there's an environment/profile suffix
        parts = name.rsplit(".", 1)
        if len(parts) > 1:
            # Check if the suffix looks like an environment/profile
            suffix = parts[1].lower()
            common_suffixes = {
                "production", "prod", "development", "dev", "staging",
                "test", "testing", "local", "default"
            }
            if suffix in common_suffixes or suffix == self._environment or suffix == self.profile:
                return parts[0]
        
        return name
    
    def _is_environment_file(self, filename: str) -> bool:
        """
            Check if a filename is an environment-specific file.
            
            :param filename: The filename to check.
            
            :returns: True if this is an environment-specific file.
        """
        if self._environment is None:
            return False
        
        path = Path(filename)
        name = path.stem  # Remove extension
        
        # Check for pattern: base.environment.ext
        env_pattern = f".{self._environment}"
        return name.lower().endswith(env_pattern.lower())
    
    def _is_profile_file(self, filename: str) -> bool:
        """
            Check if a filename is a profile-specific file.
            
            :param filename: The filename to check.
            
            :returns: True if this is a profile-specific file.
        """
        profile = self.profile
        if profile is None:
            return False
        
        path = Path(filename)
        name = path.stem  # Remove extension
        
        # Check for pattern: base.profile.ext
        profile_pattern = f".{profile}"
        return name.lower().endswith(profile_pattern.lower())
    
    def _is_base_file(self, filename: str) -> bool:
        """
            Check if a filename is a base configuration file (not env/profile specific).
            
            :param filename: The filename to check.
            
            :returns: True if this is a base configuration file.
        """
        return not self._is_environment_file(filename) and not self._is_profile_file(filename)
    
    def discover(self) -> List[Path]:
        """
            Discover configuration files in search directories.
            
            Files are returned in precedence order (lower precedence first):
            1. Base configuration files
            2. Environment-specific files
            3. Profile-specific files
            
            Within each category, files from later search directories take
            precedence over earlier ones, and within a directory files are
            taken in the order of their names.
            
            Only the base files and the files of the active environment and
            profile are returned. A file such as ``settings.dev.yaml`` is
            the ``dev`` overlay of ``settings.yaml``; it is returned when
            ``dev`` is the active environment or profile and not otherwise.
            
            :returns: List of discovered file paths in precedence order.
        """
        base_files: List[Path] = []
        env_files: List[Path] = []
        profile_files: List[Path] = []
        
        seen_files: Set[str] = set()
        
        for dir_template in self._search_directories:
            directory = self._expand_path(dir_template)
            
            if not directory.exists() or not directory.is_dir():
                continue
            
            # Find all files in the directory, in name order so that the
            # result is the same on every file system
            directory_items = sorted(directory.iterdir(), key=lambda entry: entry.name)
            for item in directory_items:
                if not item.is_file():
                    continue
                
                filename = item.name
                
                # Check if file has a supported format
                if not self._has_supported_format(filename):
                    continue
                
                # A file is discovered as a base file, as the overlay of
                # the active environment or as the overlay of the active
                # profile. A file qualified with another name (the overlay
                # of an environment or profile that is not active) is none
                # of these and is left out.
                profile = self.profile
                
                is_env_overlay = False
                if self._environment:
                    is_env_overlay = self._matches_overlay(filename, self._environment)
                
                is_profile_overlay = False
                if profile:
                    is_profile_overlay = self._matches_overlay(filename, profile)
                
                is_base = self._matches_base(filename)
                
                if not is_env_overlay and not is_profile_overlay and not is_base:
                    continue
                
                # Avoid duplicates
                file_key = str(item.resolve())
                if file_key in seen_files:
                    continue
                seen_files.add(file_key)
                
                # Categorize the file
                if is_env_overlay:
                    env_files.append(item)
                elif is_profile_overlay:
                    profile_files.append(item)
                else:
                    base_files.append(item)
        
        # Return in precedence order: base < environment < profile
        return base_files + env_files + profile_files
    
    def discover_with_precedence(self) -> List[Tuple[Path, int]]:
        """
            Discover configuration files with precedence information.
            
            Returns files with their precedence level:
            - 0: Base configuration files
            - 1: Environment-specific files
            - 2: Profile-specific files
            
            :returns: List of (path, precedence) tuples.
        """
        result: List[Tuple[Path, int]] = []
        
        files = self.discover()
        for file_path in files:
            filename = file_path.name
            
            if self._is_profile_file(filename):
                precedence = 2
            elif self._is_environment_file(filename):
                precedence = 1
            else:
                precedence = 0
            
            result.append((file_path, precedence))
        
        return result
    
    def create_file_source(
        self,
        required: bool = False,
        process_includes: bool = True
    ) -> FileSource:
        """
            Create a FileSource from discovered files.
            
            This is a convenience method that discovers files and creates
            a FileSource configured to load them in the correct precedence
            order.
            
            :param required: Whether files must exist.
            :param process_includes: Whether to process include directives.
            
            :returns: A FileSource configured with discovered files.
        """
        files = self.discover()
        return FileSource(
            paths=files,
            required=required,
            process_includes=process_includes
        )


class ProfileConfigSource(ConfigSource):
    """
        Configuration source that supports profile-based configuration.
        
        This source wraps file discovery and loading with profile support,
        automatically loading base configuration, environment-specific
        configuration, and profile-specific configuration in the correct
        precedence order.
        
        Example usage::
        
            # Load configuration with profile from APP_PROFILE env var
            source = ProfileConfigSource(
                appname="myapp",
                profile_env_var="APP_PROFILE"
            )
            
            # Load configuration with explicit profile
            source = ProfileConfigSource(
                appname="myapp",
                profile="production"
            )
        
        :param appname: Application name for file discovery.
        :param search_directories: List of directories to search.
        :param file_patterns: List of file name patterns.
        :param environment: Environment name.
        :param profile: Configuration profile name.
        :param profile_env_var: Environment variable for profile selection.
        :param supported_formats: List of supported file extensions.
    """
    
    def __init__(
        self,
        appname: str = "app",
        search_directories: Optional[List[str]] = None,
        file_patterns: Optional[List[str]] = None,
        environment: Optional[str] = None,
        profile: Optional[str] = None,
        profile_env_var: str = "APP_PROFILE",
        supported_formats: Optional[List[str]] = None
    ):
        """
            Initialize the ProfileConfigSource.
            
            :param appname: Application name for file discovery.
            :param search_directories: List of directories to search.
            :param file_patterns: List of file name patterns.
            :param environment: Environment name.
            :param profile: Configuration profile name.
            :param profile_env_var: Environment variable for profile selection.
            :param supported_formats: List of supported file extensions.
        """
        self._discovery = ConfigFileDiscovery(
            appname=appname,
            search_directories=search_directories,
            file_patterns=file_patterns,
            environment=environment,
            profile=profile,
            profile_env_var=profile_env_var,
            supported_formats=supported_formats
        )
        self._file_source: Optional[FileSource] = None
    
    @property
    def discovery(self) -> ConfigFileDiscovery:
        """
            Get the file discovery instance.
            
            :returns: The ConfigFileDiscovery instance.
        """
        return self._discovery
    
    @property
    def profile(self) -> Optional[str]:
        """
            Get the active profile.
            
            :returns: The profile name or None.
        """
        return self._discovery.profile
    
    @property
    def source_type(self) -> ConfigSourceType:
        """
            Return the source type for precedence ordering.
            
            :returns: ConfigSourceType.FILE
        """
        return ConfigSourceType.FILE
    
    def load(self) -> Dict[str, Any]:
        """
            Load configuration from discovered files.
            
            Files are loaded in precedence order:
            1. Base configuration files
            2. Environment-specific files
            3. Profile-specific files
            
            :returns: Dictionary of configuration key-value pairs.
        """
        self._file_source = self._discovery.create_file_source()
        return self._file_source.load()
    
    def get_discovered_files(self) -> List[Path]:
        """
            Get the list of discovered configuration files.
            
            :returns: List of file paths.
        """
        return self._discovery.discover()
