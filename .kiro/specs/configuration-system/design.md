# Design Document: Configuration System

## Overview

This design document describes the architecture and implementation approach for the Configuration System feature. The feature provides a unified configuration model for web applications in the ccai framework, supporting multi-source configuration loading, secrets handling, schema validation, and runtime configuration management.

The design follows a layered approach with clear separation between configuration sources, the registry that manages loading and merging, and the model that provides access to resolved values. The system integrates with the existing persona and application lifecycle infrastructure.

## Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         Application Layer                                │
│  ┌───────────────────────────────────────────────────────────────────┐  │
│  │                    Configuration_Model                             │  │
│  │  - Typed access (get_str, get_int, get_bool, etc.)                │  │
│  │  - Dot-notation access (config.database.host)                     │  │
│  │  - Dictionary access (config["database"]["host"])                 │  │
│  │  - Namespace groupings                                            │  │
│  │  - Value metadata (source, override status)                       │  │
│  └───────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                         Registry Layer                                   │
│  ┌───────────────────────────────────────────────────────────────────┐  │
│  │                    Config_Registry                                 │  │
│  │  - Source registration and management                             │  │
│  │  - Precedence-based merging                                       │  │
│  │  - Schema validation                                              │  │
│  │  - Override management                                            │  │
│  │  - Change notification                                            │  │
│  │  - Export functionality                                           │  │
│  └───────────────────────────────────────────────────────────────────┘  │
│                                    │                                     │
│           ┌────────────────────────┼────────────────────────┐           │
│           ▼                        ▼                        ▼           │
│  ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐     │
│  │ Config_Validator│    │  Config_Watcher │    │ Config_Override │     │
│  └─────────────────┘    └─────────────────┘    └─────────────────┘     │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                         Source Layer                                     │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────────────┐   │
│  │ Environment │ │ File_Source │ │  Secrets    │ │ Custom_Loader   │   │
│  │   Source    │ │ (INI/YAML/  │ │  Provider   │ │ (extensible)    │   │
│  │             │ │  JSON/TOML) │ │             │ │                 │   │
│  └─────────────┘ └─────────────┘ └─────────────┘ └─────────────────┘   │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                         Schema Layer                                     │
│  ┌───────────────────────────────────────────────────────────────────┐  │
│  │                    Config_Schema                                   │  │
│  │  - Key definitions (name, type, required, default, description)   │  │
│  │  - Nested schema support                                          │  │
│  │  - Enum constraints                                               │  │
│  │  - Custom validators                                              │  │
│  │  - Sensitive key marking                                          │  │
│  └───────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────┘
```

## Components and Interfaces

### ConfigurationModel Class

```python
class ConfigurationModel:
    """
    Unified access point for all configuration values with typed access
    and multiple access patterns.
    """
    
    def __init__(self, registry: 'ConfigRegistry'):
        """
        Args:
            registry: The configuration registry providing resolved values.
        """
        self._registry = registry
        self._cache: Dict[str, ConfigValue] = {}
    
    def get(self, key: str, default: Any = _MISSING) -> Any:
        """
        Get a configuration value by key.
        
        Args:
            key: Dot-notation key (e.g., "database.host").
            default: Default value if key not found.
        
        Returns:
            The configuration value.
        
        Raises:
            ConfigurationError: If key not found and no default provided.
        """
        pass
    
    def get_str(self, key: str, default: Optional[str] = None) -> str:
        """Get a string configuration value."""
        pass
    
    def get_int(self, key: str, default: Optional[int] = None) -> int:
        """Get an integer configuration value."""
        pass
    
    def get_float(self, key: str, default: Optional[float] = None) -> float:
        """Get a float configuration value."""
        pass
    
    def get_bool(self, key: str, default: Optional[bool] = None) -> bool:
        """Get a boolean configuration value."""
        pass
    
    def get_list(self, key: str, default: Optional[List] = None) -> List:
        """Get a list configuration value."""
        pass
    
    def get_dict(self, key: str, default: Optional[Dict] = None) -> Dict:
        """Get a dictionary configuration value."""
        pass
    
    def get_metadata(self, key: str) -> 'ConfigValueMetadata':
        """
        Get metadata about a configuration value.
        
        Args:
            key: The configuration key.
        
        Returns:
            Metadata including source and override status.
        """
        pass
    
    def namespace(self, prefix: str) -> 'ConfigNamespace':
        """
        Get a namespace view of configuration.
        
        Args:
            prefix: The namespace prefix (e.g., "database").
        
        Returns:
            A ConfigNamespace providing scoped access.
        """
        pass
    
    def __getattr__(self, name: str) -> Any:
        """Support dot-notation access (config.database.host)."""
        pass
    
    def __getitem__(self, key: str) -> Any:
        """Support dictionary-style access (config["database"]["host"])."""
        pass
```

### ConfigRegistry Class

```python
class ConfigRegistry:
    """
    Central registry managing configuration sources, loading, and merging.
    """
    
    def __init__(
        self,
        schema: Optional['ConfigSchema'] = None,
        precedence: Optional[List['ConfigSourceType']] = None
    ):
        """
        Args:
            schema: Optional schema for validation.
            precedence: Source precedence order (highest to lowest).
        """
        self._schema = schema
        self._precedence = precedence or DEFAULT_PRECEDENCE
        self._sources: Dict[ConfigSourceType, ConfigSource] = {}
        self._loaders: Dict[str, ConfigLoader] = {}
        self._overrides: Dict[str, Any] = {}
        self._callbacks: List[Callable] = []
        self._frozen = False
        self._values: Dict[str, ConfigValue] = {}
    
    def register_source(
        self,
        source_type: 'ConfigSourceType',
        source: 'ConfigSource'
    ) -> None:
        """Register a configuration source."""
        pass
    
    def register_loader(self, format: str, loader: 'ConfigLoader') -> None:
        """Register a custom configuration loader."""
        pass
    
    def load(self) -> 'ConfigurationModel':
        """
        Load configuration from all sources and return the model.
        
        Returns:
            The unified configuration model.
        
        Raises:
            ConfigurationValidationError: If validation fails.
        """
        pass
    
    def override(self, key: str, value: Any) -> None:
        """
        Set a programmatic override.
        
        Args:
            key: The configuration key.
            value: The override value.
        
        Raises:
            ConfigurationFrozenError: If configuration is frozen.
        """
        pass
    
    def freeze(self) -> None:
        """Freeze configuration to prevent further modifications."""
        pass
    
    def on_change(self, callback: Callable[['ConfigChangeEvent'], None]) -> None:
        """Register a callback for configuration changes."""
        pass
    
    def export(
        self,
        format: str,
        path: Optional[Path] = None,
        mask_secrets: bool = True
    ) -> Union[str, None]:
        """
        Export configuration to a file format.
        
        Args:
            format: Output format (ini, yaml, json, toml).
            path: Optional file path to write to.
            mask_secrets: Whether to mask sensitive values.
        
        Returns:
            Configuration string if path not provided.
        """
        pass
    
    def export_template(self, format: str) -> str:
        """Export a configuration template with defaults and descriptions."""
        pass
    
    def export_documentation(self) -> str:
        """Generate documentation for all configuration keys."""
        pass
    
    def export_diff(self) -> Dict[str, Tuple[Any, Any]]:
        """Export diff between current configuration and defaults."""
        pass
```

### ConfigSource Abstract Base Class

```python
class ConfigSource(ABC):
    """Abstract base class for configuration sources."""
    
    @abstractmethod
    def load(self) -> Dict[str, Any]:
        """
        Load configuration values from this source.
        
        Returns:
            Dictionary of configuration key-value pairs.
        """
        pass
    
    @property
    @abstractmethod
    def source_type(self) -> 'ConfigSourceType':
        """Return the source type for precedence ordering."""
        pass
```

### EnvironmentSource Class

```python
class EnvironmentSource(ConfigSource):
    """Configuration source that reads from environment variables."""
    
    def __init__(
        self,
        prefix: str = "APP_",
        separator: str = "_",
        lowercase_keys: bool = True
    ):
        """
        Args:
            prefix: Environment variable prefix (e.g., "APP_").
            separator: Separator for nested keys (e.g., "_" for APP_DATABASE_HOST).
            lowercase_keys: Whether to lowercase resulting keys.
        """
        self._prefix = prefix
        self._separator = separator
        self._lowercase_keys = lowercase_keys
    
    def load(self) -> Dict[str, Any]:
        """Load configuration from environment variables."""
        pass
    
    @property
    def source_type(self) -> ConfigSourceType:
        return ConfigSourceType.ENVIRONMENT
```

### FileSource Class

```python
class FileSource(ConfigSource):
    """Configuration source that reads from files."""
    
    def __init__(
        self,
        paths: List[Path],
        format: Optional[str] = None,
        required: bool = False
    ):
        """
        Args:
            paths: List of file paths to load (in precedence order).
            format: File format (auto-detected from extension if not provided).
            required: Whether files must exist.
        """
        self._paths = paths
        self._format = format
        self._required = required
    
    def load(self) -> Dict[str, Any]:
        """Load configuration from files."""
        pass
    
    @property
    def source_type(self) -> ConfigSourceType:
        return ConfigSourceType.FILE
```

### SecretsProvider Class

```python
class SecretsProvider(ConfigSource):
    """Configuration source for sensitive values with security features."""
    
    def __init__(
        self,
        env_prefix: str = "SECRET_",
        secrets_file: Optional[Path] = None,
        encryption_key: Optional[bytes] = None,
        audit_logger: Optional['AuditLogger'] = None
    ):
        """
        Args:
            env_prefix: Prefix for secret environment variables.
            secrets_file: Path to encrypted secrets file.
            encryption_key: Key for decrypting secrets file.
            audit_logger: Optional logger for audit trail.
        """
        self._env_prefix = env_prefix
        self._secrets_file = secrets_file
        self._encryption_key = encryption_key
        self._audit_logger = audit_logger
        self._secrets: Dict[str, SecretValue] = {}
    
    def load(self) -> Dict[str, Any]:
        """Load secrets from configured sources."""
        pass
    
    def get_secret(self, key: str) -> 'SecretValue':
        """
        Get a secret value with audit logging.
        
        Args:
            key: The secret key.
        
        Returns:
            SecretValue wrapper.
        """
        pass
    
    def reload(self) -> None:
        """Reload secrets from sources (for rotation support)."""
        pass
    
    @property
    def source_type(self) -> ConfigSourceType:
        return ConfigSourceType.SECRETS
```

### SecretValue Class

```python
class SecretValue:
    """
    Wrapper for sensitive values that prevents accidental exposure.
    """
    
    def __init__(self, value: str, key: str, audit_logger: Optional['AuditLogger'] = None):
        """
        Args:
            value: The secret value.
            key: The configuration key (for audit logging).
            audit_logger: Optional audit logger.
        """
        self._value = value
        self._key = key
        self._audit_logger = audit_logger
    
    def get_secret_value(self) -> str:
        """
        Get the underlying secret value.
        
        Returns:
            The actual secret string.
        """
        if self._audit_logger:
            self._audit_logger.log_access(self._key)
        return self._value
    
    def __str__(self) -> str:
        """Return masked representation."""
        return "***MASKED***"
    
    def __repr__(self) -> str:
        """Return masked representation."""
        return f"SecretValue(key='{self._key}', value='***MASKED***')"
```

### ConfigSchema Class

```python
class ConfigSchema:
    """
    Schema definition for configuration validation.
    """
    
    def __init__(self):
        self._keys: Dict[str, ConfigKeyDefinition] = {}
        self._nested: Dict[str, 'ConfigSchema'] = {}
    
    def define(
        self,
        key: str,
        type: Type,
        required: bool = False,
        default: Any = None,
        description: str = "",
        sensitive: bool = False,
        choices: Optional[List[Any]] = None,
        validator: Optional[Callable[[Any], bool]] = None
    ) -> 'ConfigSchema':
        """
        Define a configuration key.
        
        Args:
            key: The configuration key name.
            type: Expected type (str, int, float, bool, list, dict).
            required: Whether the key is required.
            default: Default value if not provided.
            description: Human-readable description.
            sensitive: Whether this is a sensitive value.
            choices: Optional list of valid values (enum constraint).
            validator: Optional custom validation function.
        
        Returns:
            Self for method chaining.
        """
        pass
    
    def nested(self, prefix: str, schema: 'ConfigSchema') -> 'ConfigSchema':
        """
        Add a nested schema for a configuration namespace.
        
        Args:
            prefix: The namespace prefix.
            schema: The nested schema.
        
        Returns:
            Self for method chaining.
        """
        pass
    
    def validate(self, values: Dict[str, Any]) -> List['ValidationError']:
        """
        Validate configuration values against the schema.
        
        Args:
            values: Configuration values to validate.
        
        Returns:
            List of validation errors (empty if valid).
        """
        pass
```

### ConfigWatcher Class

```python
class ConfigWatcher:
    """
    Monitors configuration files for changes and triggers reloads.
    """
    
    def __init__(self, registry: ConfigRegistry):
        """
        Args:
            registry: The configuration registry to notify on changes.
        """
        self._registry = registry
        self._watched_paths: Set[Path] = set()
        self._running = False
    
    def watch(self, path: Path) -> None:
        """Add a path to watch for changes."""
        pass
    
    def start(self) -> None:
        """Start watching for file changes."""
        pass
    
    def stop(self) -> None:
        """Stop watching for file changes."""
        pass
```

## Data Models

### ConfigSourceType Enum

```python
class ConfigSourceType(Enum):
    """Types of configuration sources with default precedence order."""
    OVERRIDE = 1      # Programmatic overrides (highest precedence)
    ENVIRONMENT = 2   # Environment variables
    SECRETS = 3       # Secrets provider
    FILE = 4          # Configuration files
    DEFAULT = 5       # Schema defaults (lowest precedence)
```

### ConfigValue Dataclass

```python
@dataclass
class ConfigValue:
    """A resolved configuration value with metadata."""
    key: str
    value: Any
    source: ConfigSourceType
    source_detail: str  # e.g., "ENV:APP_DATABASE_HOST" or "FILE:settings.yaml"
    is_override: bool
    is_sensitive: bool
```

### ConfigValueMetadata Dataclass

```python
@dataclass
class ConfigValueMetadata:
    """Metadata about a configuration value."""
    source: ConfigSourceType
    source_detail: str
    is_override: bool
    is_sensitive: bool
    schema_type: Optional[Type]
    schema_default: Any
    schema_description: str
```

### ConfigKeyDefinition Dataclass

```python
@dataclass
class ConfigKeyDefinition:
    """Definition of a configuration key in the schema."""
    key: str
    type: Type
    required: bool
    default: Any
    description: str
    sensitive: bool
    choices: Optional[List[Any]]
    validator: Optional[Callable[[Any], bool]]
```

### ConfigChangeEvent Dataclass

```python
@dataclass
class ConfigChangeEvent:
    """Event fired when configuration changes."""
    key: str
    old_value: Any
    new_value: Any
    source: ConfigSourceType
    timestamp: datetime
```

### ValidationError Dataclass

```python
@dataclass
class ValidationError:
    """A configuration validation error."""
    key: str
    message: str
    expected_type: Optional[Type]
    actual_value: Any
    constraint: Optional[str]  # e.g., "required", "type", "choices", "custom"
```



## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system—essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*

### Property 1: Typed Access Consistency

*For any* configuration value and target type, when the value is retrieved using a typed accessor (get_str, get_int, get_bool, etc.), the returned value SHALL be of the declared type or a ConfigurationError SHALL be raised if coercion is not possible.

**Validates: Requirements 1.2**

### Property 2: Access Method Equivalence

*For any* configuration key, accessing the value via dot-notation (config.database.host), dictionary-style (config["database"]["host"]), and get method (config.get("database.host")) SHALL return the same value.

**Validates: Requirements 1.3, 1.4**

### Property 3: Default Value Resolution

*For any* configuration key that is not present in any source, when a default value is specified in the access call, the default value SHALL be returned.

**Validates: Requirements 1.5**

### Property 4: Missing Required Key Error

*For any* configuration key that is marked as required in the schema and is not present in any source, accessing that key without a default SHALL raise ConfigurationError.

**Validates: Requirements 1.6**

### Property 5: Value Source Metadata

*For any* configuration value, the metadata SHALL accurately reflect the source from which the value was loaded and whether it was overridden.

**Validates: Requirements 1.8**

### Property 6: File Format Round-Trip

*For any* valid configuration dictionary, exporting to a file format (INI, YAML, JSON, TOML) and then loading from that file SHALL produce an equivalent configuration dictionary.

**Validates: Requirements 2.2, 2.3, 2.4, 2.5**

### Property 7: Source Precedence

*For any* configuration key that exists in multiple sources, the value from the highest-precedence source according to the configured precedence order SHALL be returned.

**Validates: Requirements 2.6, 2.9**

### Property 8: Environment Variable Mapping

*For any* environment variable with the configured prefix, the variable SHALL be mapped to the correct configuration key using the configured separator and case transformation rules.

**Validates: Requirements 2.10**

### Property 9: Schema Validation Completeness

*For any* configuration and schema, validation SHALL check all values against their schema definitions, and if any validation fails, ConfigurationValidationError SHALL be raised with details about all failures.

**Validates: Requirements 3.1, 3.2, 3.6, 3.7**

### Property 10: Type Coercion

*For any* string configuration value and declared type in the schema, the value SHALL be coerced to the declared type (e.g., "true" to True, "42" to 42) when possible.

**Validates: Requirements 3.8**

### Property 11: Nested Schema Validation

*For any* nested configuration structure with a nested schema definition, validation SHALL recursively validate all nested values against their respective schema definitions.

**Validates: Requirements 3.9**

### Property 12: Enum Constraint Validation

*For any* configuration key with an enum constraint (choices), values outside the allowed choices SHALL fail validation.

**Validates: Requirements 3.10**

### Property 13: Secret Encryption Round-Trip

*For any* secret value, encrypting and writing to a secrets file, then loading and decrypting SHALL produce the original secret value.

**Validates: Requirements 4.1**

### Property 14: Secret Masking

*For any* configuration key marked as sensitive, the value SHALL be masked in string representations, logs, and error messages.

**Validates: Requirements 4.4, 4.5**

### Property 15: SecretValue Wrapper Behavior

*For any* sensitive configuration value, accessing the value SHALL return a SecretValue wrapper, and calling get_secret_value() on the wrapper SHALL return the actual value.

**Validates: Requirements 4.6, 4.7**

### Property 16: Secret Audit Logging

*For any* access to a sensitive value when audit logging is enabled, an audit log entry SHALL be created recording the access.

**Validates: Requirements 4.9**

### Property 17: File Discovery

*For any* configured search directory and file name pattern, configuration files matching the pattern in those directories SHALL be discovered and loaded.

**Validates: Requirements 5.1, 5.3**

### Property 18: Environment-Specific Files

*For any* active environment/profile, the corresponding environment-specific configuration file (e.g., settings.production.yaml) SHALL be loaded and merged with the base configuration.

**Validates: Requirements 5.4**

### Property 19: File Merge Precedence

*For any* set of configuration files with overlapping keys, the files SHALL be merged according to the configured precedence order.

**Validates: Requirements 5.5**

### Property 20: Include Directive Processing

*For any* configuration file with include directives, the included files SHALL be loaded and merged into the configuration.

**Validates: Requirements 5.7**

### Property 21: Missing File Error

*For any* referenced configuration file that does not exist, ConfigurationFileNotFoundError SHALL be raised.

**Validates: Requirements 5.8**

### Property 22: Runtime Override Precedence

*For any* programmatic override, the override value SHALL take precedence over all other sources when accessing that key.

**Validates: Requirements 6.1, 6.2**

### Property 23: Change Notification Callbacks

*For any* registered change callback and configuration change, the callback SHALL be invoked with a ConfigChangeEvent containing the old value, new value, and source.

**Validates: Requirements 6.5**

### Property 24: Atomic Updates

*For any* configuration update involving multiple keys, either all changes SHALL be applied or none SHALL be applied (atomicity).

**Validates: Requirements 6.6**

### Property 25: Configuration Freeze

*For any* frozen configuration, attempting to modify values via override() SHALL raise ConfigurationFrozenError.

**Validates: Requirements 6.7, 6.8**

### Property 26: Export Round-Trip

*For any* configuration, exporting and then importing SHALL produce an equivalent configuration (excluding sensitive values if masked).

**Validates: Requirements 7.1**

### Property 27: Documentation Completeness

*For any* configuration schema, the generated documentation SHALL include key name, type, default value, description, and required status for every defined key.

**Validates: Requirements 7.2, 7.3, 7.4**

### Property 28: Export Diff Accuracy

*For any* configuration, the exported diff SHALL contain exactly the keys whose values differ from their schema defaults.

**Validates: Requirements 7.6**

### Property 29: Export Secret Masking

*For any* export operation with mask_secrets=True (the default), sensitive values SHALL be masked in the output.

**Validates: Requirements 7.7**

### Property 30: Lazy Loading

*For any* configuration with lazy loading enabled, values SHALL only be loaded from sources when first accessed.

**Validates: Requirements 8.3**

### Property 31: Profile Configuration

*For any* active profile selected via environment variable, the profile-specific configuration SHALL be loaded and merged with base configuration, with profile values taking precedence.

**Validates: Requirements 8.6, 8.7, 8.8**

## Error Handling

### ConfigurationError

Base exception for configuration-related errors.

```python
class ConfigurationError(Exception):
    """Base exception for configuration errors."""
    
    def __init__(self, message: str, key: Optional[str] = None):
        self.key = key
        super().__init__(message)
```

### ConfigurationValidationError

Raised when configuration validation fails.

```python
class ConfigurationValidationError(ConfigurationError):
    """Raised when configuration validation fails."""
    
    def __init__(self, errors: List[ValidationError]):
        self.errors = errors
        message = f"Configuration validation failed with {len(errors)} error(s):\n"
        for error in errors:
            message += f"  - {error.key}: {error.message}\n"
        super().__init__(message)
```

### ConfigurationFileNotFoundError

Raised when a referenced configuration file does not exist.

```python
class ConfigurationFileNotFoundError(ConfigurationError):
    """Raised when a configuration file is not found."""
    
    def __init__(self, path: Path, referenced_from: Optional[Path] = None):
        self.path = path
        self.referenced_from = referenced_from
        message = f"Configuration file not found: {path}"
        if referenced_from:
            message += f" (referenced from {referenced_from})"
        super().__init__(message)
```

### ConfigurationFrozenError

Raised when attempting to modify frozen configuration.

```python
class ConfigurationFrozenError(ConfigurationError):
    """Raised when attempting to modify frozen configuration."""
    
    def __init__(self, key: str):
        super().__init__(
            f"Cannot modify configuration key '{key}': configuration is frozen",
            key=key
        )
```

### ConfigurationTypeError

Raised when type coercion fails.

```python
class ConfigurationTypeError(ConfigurationError):
    """Raised when configuration type coercion fails."""
    
    def __init__(self, key: str, expected_type: Type, actual_value: Any):
        self.expected_type = expected_type
        self.actual_value = actual_value
        super().__init__(
            f"Cannot coerce '{key}' value '{actual_value}' to type {expected_type.__name__}",
            key=key
        )
```

## Testing Strategy

### Unit Tests

Unit tests should cover:

1. **ConfigurationModel Tests**
   - Verify typed access methods return correct types
   - Verify dot-notation and dictionary access work correctly
   - Verify default value handling
   - Verify ConfigurationError on missing required keys
   - Verify namespace grouping functionality

2. **ConfigRegistry Tests**
   - Verify source registration and loading
   - Verify precedence-based merging
   - Verify override functionality
   - Verify freeze functionality
   - Verify export functionality

3. **ConfigSource Tests**
   - Verify EnvironmentSource loads variables correctly
   - Verify FileSource loads each format correctly
   - Verify SecretsProvider handles encryption/decryption

4. **ConfigSchema Tests**
   - Verify key definition and validation
   - Verify type coercion
   - Verify enum constraints
   - Verify custom validators
   - Verify nested schema validation

5. **Error Condition Tests**
   - Verify ConfigurationError on missing required keys
   - Verify ConfigurationValidationError with all failure details
   - Verify ConfigurationFileNotFoundError on missing files
   - Verify ConfigurationFrozenError on frozen modification
   - Verify ConfigurationTypeError on coercion failure

### Property-Based Tests

Property-based tests should use the `testbase` framework with minimum 100 iterations per property. Each test should be tagged with the property it validates.

**Testing Framework**: testbase (as specified in AGENTS.md)

**Property Test Configuration**:
- Minimum iterations: 100
- Tag format: `Feature: configuration-system, Property N: <property_text>`

**Generator Requirements**:
- Generate valid configuration dictionaries with various nesting depths
- Generate valid configuration keys (dot-notation strings)
- Generate values of various types (str, int, float, bool, list, dict)
- Generate valid file format content (INI, YAML, JSON, TOML)
- Generate environment variable names with configurable prefixes
- Generate schema definitions with various constraints

### Test Organization

Following the repository conventions from AGENTS.md:

```
source/testroots/ccai/tests/singlehost/webworks/configuration/
├── test_configuration_model.py    # ConfigurationModel tests
├── test_config_registry.py        # ConfigRegistry tests
├── test_environment_source.py     # EnvironmentSource tests
├── test_file_source.py            # FileSource tests
├── test_secrets_provider.py       # SecretsProvider tests
├── test_config_schema.py          # ConfigSchema tests
├── test_config_watcher.py         # ConfigWatcher tests
└── test_config_export.py          # Export functionality tests
```

### Integration Points

- Integration with `ccai.webworks.persona` for presence directory discovery
- Integration with `ccai.thisapp` for application lifecycle
- Integration with logging subsystem for audit logging
- Integration with file system for configuration file discovery and watching

