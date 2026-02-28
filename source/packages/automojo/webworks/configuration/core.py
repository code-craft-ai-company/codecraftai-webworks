"""
.. module:: core
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: Core configuration data structures and enumerations.

.. moduleauthor:: Automation Mojo LLC

This module contains the fundamental data structures used throughout the
configuration system including ConfigSourceType, ConfigValue, ConfigValueMetadata,
ConfigKeyDefinition, ValidationError, and ConfigChangeEvent.
"""

__author__ = "Automation Mojo LLC"
__copyright__ = "Copyright 2025, Automation Mojo LLC"
__credits__ = []


from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Callable, List, Optional, Type


class ConfigSourceType(Enum):
    """
        Types of configuration sources with default precedence order.
        
        This enum represents the different sources from which configuration
        values can be loaded. The integer values define the default precedence
        order, where lower values indicate higher precedence.
        
        :cvar OVERRIDE: Programmatic overrides (highest precedence, value=1).
        :cvar ENVIRONMENT: Environment variables (value=2).
        :cvar SECRETS: Secrets provider (value=3).
        :cvar FILE: Configuration files (value=4).
        :cvar DEFAULT: Schema defaults (lowest precedence, value=5).
    """
    
    OVERRIDE = 1      # Programmatic overrides (highest precedence)
    ENVIRONMENT = 2   # Environment variables
    SECRETS = 3       # Secrets provider
    FILE = 4          # Configuration files
    DEFAULT = 5       # Schema defaults (lowest precedence)
    
    @property
    def precedence(self) -> int:
        """
            Get the precedence value for this source type.
            
            Lower values indicate higher precedence.
            
            :returns: The precedence value as an integer.
        """
        return self.value
    
    def __lt__(self, other: 'ConfigSourceType') -> bool:
        """
            Compare source types by precedence.
            
            A source type is "less than" another if it has higher precedence
            (lower numeric value).
            
            :param other: The other ConfigSourceType to compare against.
            
            :returns: True if this source has higher precedence than other.
        """
        if not isinstance(other, ConfigSourceType):
            return NotImplemented
        return self.value < other.value
    
    def __le__(self, other: 'ConfigSourceType') -> bool:
        """
            Compare source types by precedence (less than or equal).
            
            :param other: The other ConfigSourceType to compare against.
            
            :returns: True if this source has higher or equal precedence.
        """
        if not isinstance(other, ConfigSourceType):
            return NotImplemented
        return self.value <= other.value
    
    def __gt__(self, other: 'ConfigSourceType') -> bool:
        """
            Compare source types by precedence.
            
            A source type is "greater than" another if it has lower precedence
            (higher numeric value).
            
            :param other: The other ConfigSourceType to compare against.
            
            :returns: True if this source has lower precedence than other.
        """
        if not isinstance(other, ConfigSourceType):
            return NotImplemented
        return self.value > other.value
    
    def __ge__(self, other: 'ConfigSourceType') -> bool:
        """
            Compare source types by precedence (greater than or equal).
            
            :param other: The other ConfigSourceType to compare against.
            
            :returns: True if this source has lower or equal precedence.
        """
        if not isinstance(other, ConfigSourceType):
            return NotImplemented
        return self.value >= other.value


# Default precedence order from highest to lowest
DEFAULT_PRECEDENCE: List[ConfigSourceType] = [
    ConfigSourceType.OVERRIDE,
    ConfigSourceType.ENVIRONMENT,
    ConfigSourceType.SECRETS,
    ConfigSourceType.FILE,
    ConfigSourceType.DEFAULT
]



@dataclass
class ConfigValue:
    """
        A resolved configuration value with metadata.
        
        This dataclass represents a configuration value that has been resolved
        from one of the configuration sources, along with metadata about its
        origin and characteristics.
        
        :param key: The configuration key in dot-notation (e.g., "database.host").
        :param value: The resolved configuration value.
        :param source: The ConfigSourceType from which this value was loaded.
        :param source_detail: Detailed source info (e.g., "ENV:APP_DATABASE_HOST").
        :param is_override: Whether this value was set via programmatic override.
        :param is_sensitive: Whether this value is marked as sensitive/secret.
    """
    
    key: str
    value: Any
    source: ConfigSourceType
    source_detail: str
    is_override: bool = False
    is_sensitive: bool = False


@dataclass
class ConfigValueMetadata:
    """
        Metadata about a configuration value.
        
        This dataclass provides detailed metadata about a configuration value
        including its source, schema information, and characteristics. It is
        returned by the get_metadata() method of ConfigurationModel.
        
        :param source: The ConfigSourceType from which the value was loaded.
        :param source_detail: Detailed source info (e.g., "FILE:settings.yaml").
        :param is_override: Whether the value was set via programmatic override.
        :param is_sensitive: Whether the value is marked as sensitive/secret.
        :param schema_type: The expected type from the schema definition.
        :param schema_default: The default value from the schema definition.
        :param schema_description: The description from the schema definition.
    """
    
    source: ConfigSourceType
    source_detail: str
    is_override: bool
    is_sensitive: bool
    schema_type: Optional[Type] = None
    schema_default: Any = None
    schema_description: str = ""


@dataclass
class ConfigKeyDefinition:
    """
        Definition of a configuration key in the schema.
        
        This dataclass defines the schema for a single configuration key,
        including its type, validation rules, default value, and documentation.
        
        :param key: The configuration key name.
        :param type: Expected type (str, int, float, bool, list, dict).
        :param required: Whether the key is required.
        :param default: Default value if not provided.
        :param description: Human-readable description for documentation.
        :param sensitive: Whether this is a sensitive value (secret).
        :param choices: Optional list of valid values (enum constraint).
        :param validator: Optional custom validation function.
    """
    
    key: str
    type: Type
    required: bool = False
    default: Any = None
    description: str = ""
    sensitive: bool = False
    choices: Optional[List[Any]] = None
    validator: Optional[Callable[[Any], bool]] = None


@dataclass
class ValidationError:
    """
        A configuration validation error.
        
        This dataclass represents a single validation error that occurred
        during configuration validation. Multiple ValidationError instances
        may be collected and raised together in a ConfigurationValidationError.
        
        :param key: The configuration key that failed validation.
        :param message: Human-readable error message.
        :param expected_type: The expected type from the schema (if type error).
        :param actual_value: The actual value that failed validation.
        :param constraint: The constraint that was violated (e.g., "required", 
                          "type", "choices", "custom").
    """
    
    key: str
    message: str
    expected_type: Optional[Type] = None
    actual_value: Any = None
    constraint: Optional[str] = None


@dataclass
class ConfigChangeEvent:
    """
        Event fired when configuration changes.
        
        This dataclass represents a configuration change event that is passed
        to registered change callbacks when a configuration value is modified
        at runtime.
        
        :param key: The configuration key that changed.
        :param old_value: The previous value (None if key was not set).
        :param new_value: The new value.
        :param source: The ConfigSourceType of the change.
        :param timestamp: When the change occurred.
    """
    
    key: str
    old_value: Any
    new_value: Any
    source: ConfigSourceType
    timestamp: datetime = field(default_factory=datetime.utcnow)


class SecretValue:
    """
        Wrapper for sensitive values that prevents accidental exposure.
        
        This class wraps sensitive configuration values to prevent them from
        being accidentally logged, printed, or exposed in error messages.
        The actual value can only be retrieved by explicitly calling the
        get_secret_value() method.
        
        When audit logging is enabled, access to the secret value is logged
        for security audit purposes.
        
        :param value: The secret value to wrap.
        :param key: The configuration key (for audit logging).
        :param audit_logger: Optional audit logger for tracking secret access.
    """
    
    # Constant for masked representation
    MASKED_VALUE = "***MASKED***"
    
    def __init__(
        self,
        value: str,
        key: str,
        audit_logger: Optional[Callable[[str], None]] = None
    ):
        """
            Initialize the SecretValue wrapper.
            
            :param value: The secret value to wrap.
            :param key: The configuration key (for audit logging).
            :param audit_logger: Optional callable that accepts a key string
                                 for logging secret access events.
        """
        self._value = value
        self._key = key
        self._audit_logger = audit_logger
    
    @property
    def key(self) -> str:
        """
            Get the configuration key associated with this secret.
            
            :returns: The configuration key string.
        """
        return self._key
    
    def get_secret_value(self) -> str:
        """
            Get the underlying secret value.
            
            This method provides explicit access to the actual secret value.
            If an audit logger was provided during construction, the access
            will be logged.
            
            :returns: The actual secret string.
        """
        if self._audit_logger is not None:
            self._audit_logger(self._key)
        return self._value
    
    def __str__(self) -> str:
        """
            Return masked representation to prevent accidental exposure.
            
            :returns: The masked value string "***MASKED***".
        """
        return self.MASKED_VALUE
    
    def __repr__(self) -> str:
        """
            Return masked representation for debugging.
            
            :returns: A string representation with the key and masked value.
        """
        return f"SecretValue(key='{self._key}', value='{self.MASKED_VALUE}')"
    
    def __eq__(self, other: object) -> bool:
        """
            Compare two SecretValue instances for equality.
            
            Two SecretValue instances are equal if they have the same key
            and the same underlying value.
            
            :param other: The other object to compare against.
            
            :returns: True if both key and value match, False otherwise.
        """
        if not isinstance(other, SecretValue):
            return NotImplemented
        return self._key == other._key and self._value == other._value
    
    def __hash__(self) -> int:
        """
            Return hash of the SecretValue.
            
            The hash is based on the key and value to ensure consistent
            behavior when used in sets or as dictionary keys.
            
            :returns: Hash value based on key and value.
        """
        return hash((self._key, self._value))
