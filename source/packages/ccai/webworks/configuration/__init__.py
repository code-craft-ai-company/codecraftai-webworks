"""
.. module:: configuration
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: Package containing configuration system infrastructure for the ccai framework.

.. moduleauthor:: Code Craft AI LLC

This package provides a unified configuration system including:

- Multi-source configuration loading (environment, files, secrets)
- Schema validation and type coercion
- Secrets handling with encryption and masking
- Runtime configuration management
- Configuration export and documentation generation
"""

__author__ = "Code Craft AI LLC"
__copyright__ = "Copyright 2025, Code Craft AI LLC"
__credits__ = []


from ccai.webworks.configuration.core import (
    ConfigSourceType,
    ConfigValue,
    ConfigValueMetadata,
    ConfigKeyDefinition,
    ValidationError,
    ConfigChangeEvent,
    SecretValue,
    DEFAULT_PRECEDENCE
)

from ccai.webworks.configuration.exceptions import (
    ConfigurationError,
    ConfigurationValidationError,
    ConfigurationFileNotFoundError,
    ConfigurationFrozenError,
    ConfigurationTypeError
)

from ccai.webworks.configuration.schema import (
    ConfigSchema,
    coerce_value
)

from ccai.webworks.configuration.sources import (
    ConfigSource,
    ConfigLoader,
    EnvironmentSource,
    IniLoader,
    YamlLoader,
    JsonLoader,
    TomlLoader,
    FileSource,
    SecretsProvider,
    FORMAT_LOADERS,
    YAML_AVAILABLE,
    TOML_AVAILABLE,
    ConfigFileDiscovery,
    ProfileConfigSource,
    DEFAULT_SEARCH_DIRECTORIES,
    DEFAULT_FILE_PATTERNS
)

from ccai.webworks.configuration.registry import ConfigRegistry

from ccai.webworks.configuration.model import (
    ConfigurationModel,
    ConfigNamespace
)

from ccai.webworks.configuration.watcher import ConfigWatcher

from ccai.webworks.configuration.lifecycle import (
    ManagedConfigRegistry,
    validate_config_eagerly,
    check_validate_config_flag,
    create_config_from_persona,
    cleanup_all_registries
)

__all__ = [
    # Core data structures
    "ConfigSourceType",
    "ConfigValue",
    "ConfigValueMetadata",
    "ConfigKeyDefinition",
    "ValidationError",
    "ConfigChangeEvent",
    "SecretValue",
    "DEFAULT_PRECEDENCE",
    # Exceptions
    "ConfigurationError",
    "ConfigurationValidationError",
    "ConfigurationFileNotFoundError",
    "ConfigurationFrozenError",
    "ConfigurationTypeError",
    # Schema
    "ConfigSchema",
    "coerce_value",
    # Sources
    "ConfigSource",
    "ConfigLoader",
    "EnvironmentSource",
    "IniLoader",
    "YamlLoader",
    "JsonLoader",
    "TomlLoader",
    "FileSource",
    "SecretsProvider",
    "FORMAT_LOADERS",
    "YAML_AVAILABLE",
    "TOML_AVAILABLE",
    "ConfigFileDiscovery",
    "ProfileConfigSource",
    "DEFAULT_SEARCH_DIRECTORIES",
    "DEFAULT_FILE_PATTERNS",
    # Registry
    "ConfigRegistry",
    # Model
    "ConfigurationModel",
    "ConfigNamespace",
    # Watcher
    "ConfigWatcher",
    # Lifecycle
    "ManagedConfigRegistry",
    "validate_config_eagerly",
    "check_validate_config_flag",
    "create_config_from_persona",
    "cleanup_all_registries"
]
