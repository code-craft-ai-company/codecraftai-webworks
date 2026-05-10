"""
.. module:: schema
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: Configuration schema definition and validation.

.. moduleauthor:: Automation Mojo LLC

This module contains the ConfigSchema class for defining configuration schemas
with type annotations, validation rules, and nested schema support.
"""

__author__ = "Automation Mojo LLC"
__copyright__ = "Copyright 2025, Automation Mojo LLC"
__credits__ = []


import json
import logging

from typing import Any, Callable, Dict, List, Optional, Type, Union

from automojo.webworks.configuration.core import (
    ConfigKeyDefinition,
    ValidationError
)


# Module-level logger. Custom validator exceptions are translated
# into ValidationError objects rather than propagated, but the
# operator wants the original traceback so a misbehaving validator
# is debuggable from the journal.
logger = logging.getLogger(__name__)


# Sentinel value for missing defaults
_MISSING = object()


class ConfigSchema:
    """
        Schema definition for configuration validation.
        
        This class provides a fluent interface for defining configuration schemas
        with support for:
        
        - Type annotations for configuration values
        - Required and optional keys
        - Default values
        - Descriptions for documentation
        - Sensitive value marking
        - Enum constraints (choices)
        - Custom validation functions
        - Nested schema definitions
        
        Example usage::
        
            schema = ConfigSchema()
            schema.define("database.host", str, default="localhost", description="Database host")
            schema.define("database.port", int, required=True, description="Database port")
            schema.define("log.level", str, choices=["DEBUG", "INFO", "WARNING", "ERROR"])
            
            # Nested schema
            db_schema = ConfigSchema()
            db_schema.define("host", str, default="localhost")
            db_schema.define("port", int, required=True)
            schema.nested("database", db_schema)
    """
    
    def __init__(self):
        """
            Initialize an empty ConfigSchema.
        """
        self._keys: Dict[str, ConfigKeyDefinition] = {}
        self._nested: Dict[str, 'ConfigSchema'] = {}
    
    @property
    def keys(self) -> Dict[str, ConfigKeyDefinition]:
        """
            Get the dictionary of key definitions.
            
            :returns: Dictionary mapping key names to ConfigKeyDefinition instances.
        """
        return self._keys
    
    @property
    def nested_schemas(self) -> Dict[str, 'ConfigSchema']:
        """
            Get the dictionary of nested schemas.
            
            :returns: Dictionary mapping prefixes to nested ConfigSchema instances.
        """
        return self._nested
    
    def define(
        self,
        key: str,
        key_type: Type,
        required: bool = False,
        default: Any = None,
        description: str = "",
        sensitive: bool = False,
        choices: Optional[List[Any]] = None,
        validator: Optional[Callable[[Any], bool]] = None
    ) -> 'ConfigSchema':
        """
            Define a configuration key.
            
            This method adds a key definition to the schema. It supports method
            chaining for fluent schema definition.
            
            :param key: The configuration key name.
            :param key_type: Expected type (str, int, float, bool, list, dict).
            :param required: Whether the key is required.
            :param default: Default value if not provided.
            :param description: Human-readable description for documentation.
            :param sensitive: Whether this is a sensitive value (secret).
            :param choices: Optional list of valid values (enum constraint).
            :param validator: Optional custom validation function that takes a value
                             and returns True if valid, False otherwise.
            
            :returns: Self for method chaining.
        """
        definition = ConfigKeyDefinition(
            key=key,
            type=key_type,
            required=required,
            default=default,
            description=description,
            sensitive=sensitive,
            choices=choices,
            validator=validator
        )
        self._keys[key] = definition
        return self
    
    def nested(self, prefix: str, schema: 'ConfigSchema') -> 'ConfigSchema':
        """
            Add a nested schema for a configuration namespace.
            
            Nested schemas allow organizing related configuration keys under
            a common prefix. During validation, nested values are validated
            against their respective nested schema.
            
            :param prefix: The namespace prefix (e.g., "database").
            :param schema: The nested ConfigSchema instance.
            
            :returns: Self for method chaining.
        """
        self._nested[prefix] = schema
        return self
    
    def get_definition(self, key: str) -> Optional[ConfigKeyDefinition]:
        """
            Get the definition for a specific key.
            
            This method looks up a key definition, checking both direct keys
            and nested schemas.
            
            :param key: The configuration key to look up.
            
            :returns: The ConfigKeyDefinition if found, None otherwise.
        """
        # Check direct keys first
        if key in self._keys:
            return self._keys[key]
        
        # Check nested schemas
        for prefix, nested_schema in self._nested.items():
            if key.startswith(prefix + "."):
                nested_key = key[len(prefix) + 1:]
                return nested_schema.get_definition(nested_key)
        
        return None
    
    def get_all_definitions(self) -> Dict[str, ConfigKeyDefinition]:
        """
            Get all key definitions including nested schemas.
            
            This method returns a flattened dictionary of all key definitions,
            with nested keys prefixed appropriately.
            
            :returns: Dictionary mapping full key paths to ConfigKeyDefinition instances.
        """
        result: Dict[str, ConfigKeyDefinition] = {}
        
        # Add direct keys
        result.update(self._keys)
        
        # Add nested keys with prefix
        for prefix, nested_schema in self._nested.items():
            nested_defs = nested_schema.get_all_definitions()
            for nested_key, definition in nested_defs.items():
                full_key = f"{prefix}.{nested_key}"
                # Create a new definition with the full key
                result[full_key] = ConfigKeyDefinition(
                    key=full_key,
                    type=definition.type,
                    required=definition.required,
                    default=definition.default,
                    description=definition.description,
                    sensitive=definition.sensitive,
                    choices=definition.choices,
                    validator=definition.validator
                )
        
        return result


    def validate(self, values: Dict[str, Any]) -> List[ValidationError]:
        """
            Validate configuration values against the schema.
            
            This method validates all provided values against their schema
            definitions, checking:
            
            - Required keys are present
            - Values match their declared types (with coercion)
            - Values are within allowed choices (enum constraints)
            - Custom validators pass
            
            :param values: Configuration values to validate.
            
            :returns: List of ValidationError instances (empty if valid).
        """
        errors: List[ValidationError] = []
        
        # Get all definitions including nested (flattened)
        all_definitions = self.get_all_definitions()
        
        # Check required keys and validate present values
        for key, definition in all_definitions.items():
            value = self._get_nested_value(values, key)
            
            # Check required constraint
            if definition.required and value is None:
                errors.append(ValidationError(
                    key=key,
                    message=f"Required key '{key}' is missing",
                    constraint="required"
                ))
                continue
            
            # Skip validation if value is not present and not required
            if value is None:
                continue
            
            # Validate type (with coercion attempt)
            type_error = self._validate_type(key, value, definition.type)
            if type_error is not None:
                errors.append(type_error)
                continue
            
            # Coerce value for further validation
            coerced_value = coerce_value(value, definition.type)
            
            # Validate choices constraint
            if definition.choices is not None:
                if coerced_value not in definition.choices:
                    errors.append(ValidationError(
                        key=key,
                        message=f"Value '{coerced_value}' is not in allowed choices: {definition.choices}",
                        actual_value=coerced_value,
                        constraint="choices"
                    ))
                    continue
            
            # Validate custom validator
            if definition.validator is not None:
                try:
                    if not definition.validator(coerced_value):
                        errors.append(ValidationError(
                            key=key,
                            message=f"Custom validation failed for key '{key}'",
                            actual_value=coerced_value,
                            constraint="custom"
                        ))
                except Exception as e:
                    logger.exception(
                        "ConfigSchema: custom validator for key=%s raised", key
                    )
                    errors.append(ValidationError(
                        key=key,
                        message=f"Custom validator raised exception: {e}",
                        actual_value=coerced_value,
                        constraint="custom"
                    ))
        
        return errors
    
    def _get_nested_value(self, values: Dict[str, Any], key: str) -> Any:
        """
            Get a value from a nested dictionary using dot notation.
            
            :param values: The dictionary to search.
            :param key: The dot-notation key (e.g., "database.host").
            
            :returns: The value if found, None otherwise.
        """
        parts = key.split(".")
        current = values
        
        for part in parts:
            if not isinstance(current, dict):
                return None
            if part not in current:
                return None
            current = current[part]
        
        return current
    
    def _validate_type(
        self,
        key: str,
        value: Any,
        expected_type: Type
    ) -> Optional[ValidationError]:
        """
            Validate that a value can be coerced to the expected type.
            
            :param key: The configuration key.
            :param value: The value to validate.
            :param expected_type: The expected type.
            
            :returns: ValidationError if type validation fails, None otherwise.
        """
        try:
            coerce_value(value, expected_type)
            return None
        except (ValueError, TypeError, json.JSONDecodeError):
            return ValidationError(
                key=key,
                message=f"Cannot coerce value '{value}' to type {expected_type.__name__}",
                expected_type=expected_type,
                actual_value=value,
                constraint="type"
            )


def coerce_value(value: Any, target_type: Type) -> Any:
    """
        Coerce a value to the target type.
        
        This function attempts to convert a value to the specified type,
        supporting common coercions like string to int, float, bool, list, and dict.
        
        Supported coercions:
        
        - str to int: "42" -> 42
        - str to float: "3.14" -> 3.14
        - str to bool: "true", "yes", "1", "on" -> True; "false", "no", "0", "off" -> False
        - str to list: JSON parsing of array strings
        - str to dict: JSON parsing of object strings
        
        :param value: The value to coerce.
        :param target_type: The target type to coerce to.
        
        :returns: The coerced value.
        
        :raises ValueError: If the value cannot be coerced to the target type.
        :raises TypeError: If the value type is incompatible with the target type.
    """
    # If already the correct type, return as-is
    if isinstance(value, target_type):
        # Special case: bool is a subclass of int, so we need to check explicitly
        if target_type is int and isinstance(value, bool):
            pass  # Continue to coercion
        else:
            return value
    
    # Handle None
    if value is None:
        return None
    
    # String coercions
    if isinstance(value, str):
        if target_type is int:
            return int(value)
        
        if target_type is float:
            return float(value)
        
        if target_type is bool:
            return _coerce_string_to_bool(value)
        
        if target_type is list:
            return _coerce_string_to_list(value)
        
        if target_type is dict:
            return _coerce_string_to_dict(value)
        
        if target_type is str:
            return value
    
    # Numeric coercions
    if isinstance(value, (int, float)):
        if target_type is int:
            return int(value)
        
        if target_type is float:
            return float(value)
        
        if target_type is str:
            return str(value)
        
        if target_type is bool:
            return bool(value)
    
    # Bool to other types
    if isinstance(value, bool):
        if target_type is int:
            return int(value)
        
        if target_type is str:
            return str(value).lower()
    
    # List coercions
    if isinstance(value, list):
        if target_type is str:
            return json.dumps(value)
        
        if target_type is list:
            return value
    
    # Dict coercions
    if isinstance(value, dict):
        if target_type is str:
            return json.dumps(value)
        
        if target_type is dict:
            return value
    
    # If we get here, coercion is not supported
    raise TypeError(
        f"Cannot coerce value of type {type(value).__name__} to {target_type.__name__}"
    )


def _coerce_string_to_bool(value: str) -> bool:
    """
        Coerce a string value to boolean.
        
        :param value: The string value to coerce.
        
        :returns: The boolean value.
        
        :raises ValueError: If the string cannot be interpreted as a boolean.
    """
    lower_value = value.lower().strip()
    
    if lower_value in ("true", "yes", "1", "on", "t", "y"):
        return True
    
    if lower_value in ("false", "no", "0", "off", "f", "n"):
        return False
    
    raise ValueError(f"Cannot coerce '{value}' to bool")


def _coerce_string_to_list(value: str) -> list:
    """
        Coerce a string value to a list using JSON parsing.
        
        :param value: The string value to coerce.
        
        :returns: The list value.
        
        :raises ValueError: If the string cannot be parsed as a JSON array.
    """
    stripped = value.strip()
    
    # Try JSON parsing
    try:
        result = json.loads(stripped)
        if isinstance(result, list):
            return result
        raise ValueError(f"JSON value is not a list: {type(result).__name__}")
    except json.JSONDecodeError as e:
        raise ValueError(f"Cannot parse '{value}' as JSON list: {e}")


def _coerce_string_to_dict(value: str) -> dict:
    """
        Coerce a string value to a dict using JSON parsing.
        
        :param value: The string value to coerce.
        
        :returns: The dict value.
        
        :raises ValueError: If the string cannot be parsed as a JSON object.
    """
    stripped = value.strip()
    
    # Try JSON parsing
    try:
        result = json.loads(stripped)
        if isinstance(result, dict):
            return result
        raise ValueError(f"JSON value is not a dict: {type(result).__name__}")
    except json.JSONDecodeError as e:
        raise ValueError(f"Cannot parse '{value}' as JSON dict: {e}")
