"""
.. module:: configuration
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: Package containing configuration system infrastructure for the automojo framework.

.. moduleauthor:: Automation Mojo LLC

This package provides a unified configuration system including:

- Multi-source configuration loading (environment, files, secrets)
- Schema validation and type coercion
- Secrets handling with encryption and masking
- Runtime configuration management
- Configuration export and documentation generation
"""

__author__ = "Automation Mojo LLC"
__copyright__ = "Copyright 2025, Automation Mojo LLC"
__credits__ = []


from automojo.webworks.configuration.core import (
    ConfigSourceType,
    ConfigValue,
    ConfigValueMetadata,
    ConfigKeyDefinition,
    ValidationError,
    ConfigChangeEvent,
    SecretValue,
    DEFAULT_PRECEDENCE
)

from automojo.webworks.configuration.exceptions import (
    ConfigurationError,
    ConfigurationValidationError,
    ConfigurationFileNotFoundError,
    ConfigurationFrozenError,
    ConfigurationTypeError
)

from automojo.webworks.configuration.schema import (
    ConfigSchema,
    coerce_value
)

from automojo.webworks.configuration.sources import (
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

from automojo.webworks.configuration.registry import ConfigRegistry

from automojo.webworks.configuration.model import (
    ConfigurationModel,
    ConfigNamespace
)

from automojo.webworks.configuration.watcher import ConfigWatcher

from automojo.webworks.configuration.lifecycle import (
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
