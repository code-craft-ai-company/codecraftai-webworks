"""
.. module:: sources
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: Configuration source implementations for loading configuration values.

.. moduleauthor:: Automation Mojo LLC

This module contains the abstract ConfigSource base class and concrete implementations
for loading configuration from various sources including environment variables,
files, and secrets providers.
"""

__author__ = "Automation Mojo LLC"
__copyright__ = "Copyright 2025, Automation Mojo LLC"
__credits__ = []


import configparser
import json
import logging
import os

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Set, Tuple, Union

from automojo.webworks.configuration.core import ConfigSourceType, SecretValue
from automojo.webworks.configuration.exceptions import (
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
            and optionally lowercases the result.
            
            :param env_name: The environment variable name.
            
            :returns: The transformed configuration key.
        """
        # Remove the prefix
        key = env_name[len(self._prefix):]
        
        # Replace separator with dots
        key = key.replace(self._separator, ".")
        
        # Optionally lowercase
        if self._lowercase_keys:
            key = key.lower()
        
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
        a section prefix.
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
        parser = configparser.ConfigParser()
        
        try:
            parser.read_string(content)
        except configparser.Error as e:
            logger.warning("INI loader: parse failure: %s", e)
            raise ConfigurationError(f"Failed to parse INI content: {e}") from e
        
        result: Dict[str, Any] = {}
        
        # Process DEFAULT section (top-level keys)
        for key, value in parser.defaults().items():
            result[key] = value
        
        # Process named sections
        for section in parser.sections():
            for key, value in parser.items(section):
                # Skip keys that are in defaults (they're inherited)
                if key in parser.defaults():
                    continue
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
        parser = configparser.ConfigParser()
        
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


# Include directive patterns for different formats
INCLUDE_PATTERNS = {
    "ini": r'^\s*%include\s+["\']?([^"\']+)["\']?\s*$',
    "yaml": r'^\s*#\s*!include\s+["\']?([^"\']+)["\']?\s*$',
    "json": None,  # JSON doesn't support comments, so no include directive
    "toml": r'^\s*#\s*!include\s+["\']?([^"\']+)["\']?\s*$',
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
    
    def _process_include_directives(
        self,
        content: str,
        format: str,
        base_path: Path,
        visited: Optional[set] = None
    ) -> str:
        """
            Process include directives in configuration content.
            
            :param content: The configuration content.
            :param format: The file format.
            :param base_path: The base path for resolving relative includes.
            :param visited: Set of already visited paths (for cycle detection).
            
            :returns: The content with includes expanded.
            
            :raises ConfigurationFileNotFoundError: If included file not found.
            :raises ConfigurationError: If circular include detected.
        """
        import re
        
        if visited is None:
            visited = set()
        
        # Get the include pattern for this format
        pattern_str = INCLUDE_PATTERNS.get(format)
        if not pattern_str:
            return content
        
        pattern = re.compile(pattern_str, re.MULTILINE)
        
        def replace_include(match):
            include_path_str = match.group(1).strip()
            
            # Resolve relative path
            if not os.path.isabs(include_path_str):
                include_path = base_path.parent / include_path_str
            else:
                include_path = Path(include_path_str)
            
            include_path = include_path.resolve()
            
            # Check for circular includes
            if include_path in visited:
                raise ConfigurationError(
                    f"Circular include detected: {include_path}"
                )
            
            # Check if file exists
            if not include_path.exists():
                raise ConfigurationFileNotFoundError(
                    include_path,
                    referenced_from=base_path
                )
            
            # Read and recursively process the included file
            visited.add(include_path)
            included_content = include_path.read_text()
            
            # Recursively process includes in the included file
            included_content = self._process_include_directives(
                included_content,
                format,
                include_path,
                visited
            )
            
            return included_content
        
        return pattern.sub(replace_include, content)
    
    def _load_file(
        self,
        path: Path,
        visited: Optional[set] = None
    ) -> Dict[str, Any]:
        """
            Load configuration from a single file.
            
            :param path: The file path.
            :param visited: Set of already visited paths (for include processing).
            
            :returns: Dictionary of configuration key-value pairs.
            
            :raises ConfigurationFileNotFoundError: If file not found and required.
            :raises ConfigurationError: If loading fails.
        """
        if not path.exists():
            if self._required:
                raise ConfigurationFileNotFoundError(path)
            return {}
        
        # Get format and loader
        format = self._get_format(path)
        loader = self._get_loader(format)
        
        # Read file content
        content = path.read_text()
        
        # Process include directives if enabled
        if self._process_includes:
            if visited is None:
                visited = {path.resolve()}
            content = self._process_include_directives(
                content,
                format,
                path,
                visited
            )
        
        # Parse content
        return loader.load(content)
    
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
    """
    
    # AES block size for encryption
    AES_BLOCK_SIZE = 16
    
    # Salt size for key derivation
    SALT_SIZE = 16
    
    # Number of iterations for key derivation
    KDF_ITERATIONS = 100000
    
    def __init__(
        self,
        env_prefix: str = "SECRET_",
        secrets_file: Optional[Path] = None,
        encryption_key: Optional[bytes] = None,
        audit_logger: Optional[Callable[[str], None]] = None
    ):
        """
            Initialize the SecretsProvider.
            
            :param env_prefix: Prefix for secret environment variables.
            :param secrets_file: Path to encrypted secrets file.
            :param encryption_key: Key for decrypting secrets file.
            :param audit_logger: Optional logger for audit trail.
        """
        self._env_prefix = env_prefix
        self._secrets_file = Path(secrets_file) if secrets_file else None
        self._encryption_key = encryption_key
        self._audit_logger = audit_logger
        self._secrets: Dict[str, 'SecretValue'] = {}
        self._loaded = False
    
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
            and lowercases the result.
            
            :param env_name: The environment variable name.
            
            :returns: The transformed configuration key.
        """
        # Remove the prefix
        key = env_name[len(self._env_prefix):]
        
        # Replace underscores with dots
        key = key.replace("_", ".")
        
        # Lowercase
        key = key.lower()
        
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
            
            :raises ConfigurationFileNotFoundError: If secrets file not found.
            :raises ConfigurationError: If loading fails.
        """
        # Load from environment
        secrets = self._load_from_environment()
        
        # Load from file (overrides environment)
        if self._secrets_file is not None and self._secrets_file.exists():
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
            
            Uses AES-256-CBC encryption with PBKDF2 key derivation.
            
            :param secrets_data: Dictionary of secret key-value pairs.
            
            :returns: Encrypted bytes.
            
            :raises ConfigurationError: If encryption fails or key not provided.
        """
        if self._encryption_key is None:
            raise ConfigurationError(
                "Encryption key required to encrypt secrets"
            )
        
        try:
            from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
            from cryptography.hazmat.primitives import padding
            from cryptography.hazmat.backends import default_backend
        except ImportError:
            raise ConfigurationError(
                "cryptography package required for secrets encryption. "
                "Install with: pip install cryptography"
            )
        
        # Convert to JSON
        plaintext = json.dumps(secrets_data).encode('utf-8')
        
        # Generate random IV
        iv = os.urandom(self.AES_BLOCK_SIZE)
        
        # Generate random salt for key derivation
        salt = os.urandom(self.SALT_SIZE)
        
        # Derive key using PBKDF2
        derived_key = self._derive_key(self._encryption_key, salt)
        
        # Pad plaintext to block size
        padder = padding.PKCS7(self.AES_BLOCK_SIZE * 8).padder()
        padded_data = padder.update(plaintext) + padder.finalize()
        
        # Encrypt
        cipher = Cipher(
            algorithms.AES(derived_key),
            modes.CBC(iv),
            backend=default_backend()
        )
        encryptor = cipher.encryptor()
        ciphertext = encryptor.update(padded_data) + encryptor.finalize()
        
        # Return salt + iv + ciphertext
        return salt + iv + ciphertext
    
    def decrypt_secrets(self, encrypted_data: bytes) -> str:
        """
            Decrypt secrets data from file.
            
            :param encrypted_data: Encrypted bytes (salt + iv + ciphertext).
            
            :returns: Decrypted JSON string.
            
            :raises ConfigurationError: If decryption fails.
        """
        if self._encryption_key is None:
            raise ConfigurationError(
                "Encryption key required to decrypt secrets"
            )
        
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
        derived_key = self._derive_key(self._encryption_key, salt)
        
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
    
    def _derive_key(self, password: bytes, salt: bytes) -> bytes:
        """
            Derive an encryption key from password using PBKDF2.
            
            :param password: The password/key bytes.
            :param salt: Random salt bytes.
            
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
        
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,  # 256 bits for AES-256
            salt=salt,
            iterations=self.KDF_ITERATIONS,
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
import re


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
        
        1. Search directories are checked in order
        2. Files matching the configured patterns are discovered
        3. Environment-specific files (e.g., settings.production.yaml) are
           discovered when an environment is specified
        4. Profile-specific files are discovered when a profile is active
        
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
            precedence over earlier ones.
            
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
            
            # Find all files in the directory
            for item in directory.iterdir():
                if not item.is_file():
                    continue
                
                filename = item.name
                
                # Check if file has a supported format
                if not self._has_supported_format(filename):
                    continue
                
                # Check if file matches any pattern
                matches_pattern = False
                for pattern in self._file_patterns:
                    if self._matches_pattern(filename, pattern):
                        matches_pattern = True
                        break
                    
                    # Also check environment-specific patterns
                    if self._environment:
                        env_pattern = pattern.replace(".*", f".{self._environment}.*")
                        if self._matches_pattern(filename, env_pattern):
                            matches_pattern = True
                            break
                    
                    # Also check profile-specific patterns
                    profile = self.profile
                    if profile:
                        profile_pattern = pattern.replace(".*", f".{profile}.*")
                        if self._matches_pattern(filename, profile_pattern):
                            matches_pattern = True
                            break
                
                if not matches_pattern:
                    continue
                
                # Avoid duplicates
                file_key = str(item.resolve())
                if file_key in seen_files:
                    continue
                seen_files.add(file_key)
                
                # Categorize the file
                if self._is_environment_file(filename):
                    env_files.append(item)
                elif self._is_profile_file(filename):
                    profile_files.append(item)
                elif self._is_base_file(filename):
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
