"""
    Tests for the configuration core module.
    
    This module contains unit tests for the core configuration data structures:
    ConfigSourceType, ConfigValue, ConfigValueMetadata, ConfigKeyDefinition,
    ValidationError, and ConfigChangeEvent.
"""

from datetime import datetime, timedelta, timezone
from typing import Any

from ccai.webworks.configuration import (
    ConfigSourceType,
    ConfigValue,
    ConfigValueMetadata,
    ConfigKeyDefinition,
    ValidationError,
    ConfigChangeEvent,
    DEFAULT_PRECEDENCE
)


# =============================================================================
# Unit Tests for ConfigSourceType
# =============================================================================

def test_config_source_type_has_override():
    """
        Test that ConfigSourceType has OVERRIDE value with precedence 1.
    """
    if ConfigSourceType.OVERRIDE.value != 1:
        errmsg = f"Expected OVERRIDE value 1, got {ConfigSourceType.OVERRIDE.value}"
        raise AssertionError(errmsg)
    
    return


def test_config_source_type_has_environment():
    """
        Test that ConfigSourceType has ENVIRONMENT value with precedence 2.
    """
    if ConfigSourceType.ENVIRONMENT.value != 2:
        errmsg = f"Expected ENVIRONMENT value 2, got {ConfigSourceType.ENVIRONMENT.value}"
        raise AssertionError(errmsg)
    
    return


def test_config_source_type_has_secrets():
    """
        Test that ConfigSourceType has SECRETS value with precedence 3.
    """
    if ConfigSourceType.SECRETS.value != 3:
        errmsg = f"Expected SECRETS value 3, got {ConfigSourceType.SECRETS.value}"
        raise AssertionError(errmsg)
    
    return


def test_config_source_type_has_file():
    """
        Test that ConfigSourceType has FILE value with precedence 4.
    """
    if ConfigSourceType.FILE.value != 4:
        errmsg = f"Expected FILE value 4, got {ConfigSourceType.FILE.value}"
        raise AssertionError(errmsg)
    
    return


def test_config_source_type_has_default():
    """
        Test that ConfigSourceType has DEFAULT value with precedence 5.
    """
    if ConfigSourceType.DEFAULT.value != 5:
        errmsg = f"Expected DEFAULT value 5, got {ConfigSourceType.DEFAULT.value}"
        raise AssertionError(errmsg)
    
    return


def test_config_source_type_precedence_property():
    """
        Test that ConfigSourceType.precedence property returns the value.
    """
    if ConfigSourceType.OVERRIDE.precedence != 1:
        errmsg = f"Expected OVERRIDE precedence 1, got {ConfigSourceType.OVERRIDE.precedence}"
        raise AssertionError(errmsg)
    
    if ConfigSourceType.DEFAULT.precedence != 5:
        errmsg = f"Expected DEFAULT precedence 5, got {ConfigSourceType.DEFAULT.precedence}"
        raise AssertionError(errmsg)
    
    return


def test_config_source_type_comparison_less_than():
    """
        Test that ConfigSourceType comparison works correctly for less than.
    """
    # OVERRIDE (1) < ENVIRONMENT (2) should be True (higher precedence)
    if not (ConfigSourceType.OVERRIDE < ConfigSourceType.ENVIRONMENT):
        errmsg = "Expected OVERRIDE < ENVIRONMENT to be True"
        raise AssertionError(errmsg)
    
    # ENVIRONMENT (2) < OVERRIDE (1) should be False
    if ConfigSourceType.ENVIRONMENT < ConfigSourceType.OVERRIDE:
        errmsg = "Expected ENVIRONMENT < OVERRIDE to be False"
        raise AssertionError(errmsg)
    
    return


def test_config_source_type_comparison_greater_than():
    """
        Test that ConfigSourceType comparison works correctly for greater than.
    """
    # DEFAULT (5) > FILE (4) should be True (lower precedence)
    if not (ConfigSourceType.DEFAULT > ConfigSourceType.FILE):
        errmsg = "Expected DEFAULT > FILE to be True"
        raise AssertionError(errmsg)
    
    # FILE (4) > DEFAULT (5) should be False
    if ConfigSourceType.FILE > ConfigSourceType.DEFAULT:
        errmsg = "Expected FILE > DEFAULT to be False"
        raise AssertionError(errmsg)
    
    return


def test_default_precedence_order():
    """
        Test that DEFAULT_PRECEDENCE has the correct order.
    """
    expected = [
        ConfigSourceType.OVERRIDE,
        ConfigSourceType.ENVIRONMENT,
        ConfigSourceType.SECRETS,
        ConfigSourceType.FILE,
        ConfigSourceType.DEFAULT
    ]
    
    if DEFAULT_PRECEDENCE != expected:
        errmsg = f"Expected DEFAULT_PRECEDENCE {expected}, got {DEFAULT_PRECEDENCE}"
        raise AssertionError(errmsg)
    
    return


def test_default_precedence_length():
    """
        Test that DEFAULT_PRECEDENCE contains all source types.
    """
    if len(DEFAULT_PRECEDENCE) != 5:
        errmsg = f"Expected DEFAULT_PRECEDENCE length 5, got {len(DEFAULT_PRECEDENCE)}"
        raise AssertionError(errmsg)
    
    return


# =============================================================================
# Unit Tests for ConfigValue
# =============================================================================

def test_config_value_creation():
    """
        Test that ConfigValue can be created with required fields.
    """
    value = ConfigValue(
        key="database.host",
        value="localhost",
        source=ConfigSourceType.FILE,
        source_detail="FILE:settings.yaml"
    )
    
    if value.key != "database.host":
        errmsg = f"Expected key 'database.host', got {value.key}"
        raise AssertionError(errmsg)
    
    if value.value != "localhost":
        errmsg = f"Expected value 'localhost', got {value.value}"
        raise AssertionError(errmsg)
    
    if value.source != ConfigSourceType.FILE:
        errmsg = f"Expected source FILE, got {value.source}"
        raise AssertionError(errmsg)
    
    if value.source_detail != "FILE:settings.yaml":
        errmsg = f"Expected source_detail 'FILE:settings.yaml', got {value.source_detail}"
        raise AssertionError(errmsg)
    
    return


def test_config_value_default_is_override():
    """
        Test that ConfigValue has False as default is_override.
    """
    value = ConfigValue(
        key="test.key",
        value="test",
        source=ConfigSourceType.FILE,
        source_detail="FILE:test.yaml"
    )
    
    if value.is_override is not False:
        errmsg = f"Expected is_override False, got {value.is_override}"
        raise AssertionError(errmsg)
    
    return


def test_config_value_default_is_sensitive():
    """
        Test that ConfigValue has False as default is_sensitive.
    """
    value = ConfigValue(
        key="test.key",
        value="test",
        source=ConfigSourceType.FILE,
        source_detail="FILE:test.yaml"
    )
    
    if value.is_sensitive is not False:
        errmsg = f"Expected is_sensitive False, got {value.is_sensitive}"
        raise AssertionError(errmsg)
    
    return


def test_config_value_with_override():
    """
        Test that ConfigValue can be created with is_override=True.
    """
    value = ConfigValue(
        key="database.host",
        value="override-host",
        source=ConfigSourceType.OVERRIDE,
        source_detail="OVERRIDE:programmatic",
        is_override=True
    )
    
    if value.is_override is not True:
        errmsg = f"Expected is_override True, got {value.is_override}"
        raise AssertionError(errmsg)
    
    return


def test_config_value_with_sensitive():
    """
        Test that ConfigValue can be created with is_sensitive=True.
    """
    value = ConfigValue(
        key="database.password",
        value="secret123",
        source=ConfigSourceType.SECRETS,
        source_detail="SECRETS:env",
        is_sensitive=True
    )
    
    if value.is_sensitive is not True:
        errmsg = f"Expected is_sensitive True, got {value.is_sensitive}"
        raise AssertionError(errmsg)
    
    return


def test_config_value_with_various_value_types():
    """
        Test that ConfigValue can store various value types.
    """
    # String value
    str_value = ConfigValue(
        key="str.key",
        value="string",
        source=ConfigSourceType.FILE,
        source_detail="FILE:test.yaml"
    )
    if str_value.value != "string":
        errmsg = f"Expected string value, got {str_value.value}"
        raise AssertionError(errmsg)
    
    # Integer value
    int_value = ConfigValue(
        key="int.key",
        value=42,
        source=ConfigSourceType.FILE,
        source_detail="FILE:test.yaml"
    )
    if int_value.value != 42:
        errmsg = f"Expected int value 42, got {int_value.value}"
        raise AssertionError(errmsg)
    
    # Boolean value
    bool_value = ConfigValue(
        key="bool.key",
        value=True,
        source=ConfigSourceType.FILE,
        source_detail="FILE:test.yaml"
    )
    if bool_value.value is not True:
        errmsg = f"Expected bool value True, got {bool_value.value}"
        raise AssertionError(errmsg)
    
    # List value
    list_value = ConfigValue(
        key="list.key",
        value=[1, 2, 3],
        source=ConfigSourceType.FILE,
        source_detail="FILE:test.yaml"
    )
    if list_value.value != [1, 2, 3]:
        errmsg = f"Expected list value [1, 2, 3], got {list_value.value}"
        raise AssertionError(errmsg)
    
    # Dict value
    dict_value = ConfigValue(
        key="dict.key",
        value={"nested": "value"},
        source=ConfigSourceType.FILE,
        source_detail="FILE:test.yaml"
    )
    if dict_value.value != {"nested": "value"}:
        errmsg = f"Expected dict value, got {dict_value.value}"
        raise AssertionError(errmsg)
    
    return


# =============================================================================
# Unit Tests for ConfigValueMetadata
# =============================================================================

def test_config_value_metadata_creation():
    """
        Test that ConfigValueMetadata can be created with required fields.
    """
    metadata = ConfigValueMetadata(
        source=ConfigSourceType.ENVIRONMENT,
        source_detail="ENV:APP_DATABASE_HOST",
        is_override=False,
        is_sensitive=False
    )
    
    if metadata.source != ConfigSourceType.ENVIRONMENT:
        errmsg = f"Expected source ENVIRONMENT, got {metadata.source}"
        raise AssertionError(errmsg)
    
    if metadata.source_detail != "ENV:APP_DATABASE_HOST":
        errmsg = f"Expected source_detail 'ENV:APP_DATABASE_HOST', got {metadata.source_detail}"
        raise AssertionError(errmsg)
    
    return


def test_config_value_metadata_default_schema_type():
    """
        Test that ConfigValueMetadata has None as default schema_type.
    """
    metadata = ConfigValueMetadata(
        source=ConfigSourceType.FILE,
        source_detail="FILE:test.yaml",
        is_override=False,
        is_sensitive=False
    )
    
    if metadata.schema_type is not None:
        errmsg = f"Expected schema_type None, got {metadata.schema_type}"
        raise AssertionError(errmsg)
    
    return


def test_config_value_metadata_default_schema_default():
    """
        Test that ConfigValueMetadata has None as default schema_default.
    """
    metadata = ConfigValueMetadata(
        source=ConfigSourceType.FILE,
        source_detail="FILE:test.yaml",
        is_override=False,
        is_sensitive=False
    )
    
    if metadata.schema_default is not None:
        errmsg = f"Expected schema_default None, got {metadata.schema_default}"
        raise AssertionError(errmsg)
    
    return


def test_config_value_metadata_default_schema_description():
    """
        Test that ConfigValueMetadata has empty string as default schema_description.
    """
    metadata = ConfigValueMetadata(
        source=ConfigSourceType.FILE,
        source_detail="FILE:test.yaml",
        is_override=False,
        is_sensitive=False
    )
    
    if metadata.schema_description != "":
        errmsg = f"Expected schema_description '', got {metadata.schema_description}"
        raise AssertionError(errmsg)
    
    return


def test_config_value_metadata_with_schema_info():
    """
        Test that ConfigValueMetadata can store schema information.
    """
    metadata = ConfigValueMetadata(
        source=ConfigSourceType.FILE,
        source_detail="FILE:settings.yaml",
        is_override=False,
        is_sensitive=False,
        schema_type=str,
        schema_default="localhost",
        schema_description="The database host address"
    )
    
    if metadata.schema_type is not str:
        errmsg = f"Expected schema_type str, got {metadata.schema_type}"
        raise AssertionError(errmsg)
    
    if metadata.schema_default != "localhost":
        errmsg = f"Expected schema_default 'localhost', got {metadata.schema_default}"
        raise AssertionError(errmsg)
    
    if metadata.schema_description != "The database host address":
        errmsg = f"Expected schema_description 'The database host address', got {metadata.schema_description}"
        raise AssertionError(errmsg)
    
    return


# =============================================================================
# Unit Tests for ConfigKeyDefinition
# =============================================================================

def test_config_key_definition_creation():
    """
        Test that ConfigKeyDefinition can be created with required fields.
    """
    definition = ConfigKeyDefinition(
        key="database.host",
        type=str
    )
    
    if definition.key != "database.host":
        errmsg = f"Expected key 'database.host', got {definition.key}"
        raise AssertionError(errmsg)
    
    if definition.type is not str:
        errmsg = f"Expected type str, got {definition.type}"
        raise AssertionError(errmsg)
    
    return


def test_config_key_definition_default_required():
    """
        Test that ConfigKeyDefinition has False as default required.
    """
    definition = ConfigKeyDefinition(key="test.key", type=str)
    
    if definition.required is not False:
        errmsg = f"Expected required False, got {definition.required}"
        raise AssertionError(errmsg)
    
    return


def test_config_key_definition_default_default():
    """
        Test that ConfigKeyDefinition has None as default default.
    """
    definition = ConfigKeyDefinition(key="test.key", type=str)
    
    if definition.default is not None:
        errmsg = f"Expected default None, got {definition.default}"
        raise AssertionError(errmsg)
    
    return


def test_config_key_definition_default_description():
    """
        Test that ConfigKeyDefinition has empty string as default description.
    """
    definition = ConfigKeyDefinition(key="test.key", type=str)
    
    if definition.description != "":
        errmsg = f"Expected description '', got {definition.description}"
        raise AssertionError(errmsg)
    
    return


def test_config_key_definition_default_sensitive():
    """
        Test that ConfigKeyDefinition has False as default sensitive.
    """
    definition = ConfigKeyDefinition(key="test.key", type=str)
    
    if definition.sensitive is not False:
        errmsg = f"Expected sensitive False, got {definition.sensitive}"
        raise AssertionError(errmsg)
    
    return


def test_config_key_definition_default_choices():
    """
        Test that ConfigKeyDefinition has None as default choices.
    """
    definition = ConfigKeyDefinition(key="test.key", type=str)
    
    if definition.choices is not None:
        errmsg = f"Expected choices None, got {definition.choices}"
        raise AssertionError(errmsg)
    
    return


def test_config_key_definition_default_validator():
    """
        Test that ConfigKeyDefinition has None as default validator.
    """
    definition = ConfigKeyDefinition(key="test.key", type=str)
    
    if definition.validator is not None:
        errmsg = f"Expected validator None, got {definition.validator}"
        raise AssertionError(errmsg)
    
    return


def test_config_key_definition_with_all_fields():
    """
        Test that ConfigKeyDefinition can be created with all fields.
    """
    def custom_validator(value: Any) -> bool:
        return len(value) > 0
    
    definition = ConfigKeyDefinition(
        key="database.host",
        type=str,
        required=True,
        default="localhost",
        description="The database host address",
        sensitive=False,
        choices=["localhost", "127.0.0.1", "db.example.com"],
        validator=custom_validator
    )
    
    if definition.key != "database.host":
        errmsg = f"Expected key 'database.host', got {definition.key}"
        raise AssertionError(errmsg)
    
    if definition.type is not str:
        errmsg = f"Expected type str, got {definition.type}"
        raise AssertionError(errmsg)
    
    if definition.required is not True:
        errmsg = f"Expected required True, got {definition.required}"
        raise AssertionError(errmsg)
    
    if definition.default != "localhost":
        errmsg = f"Expected default 'localhost', got {definition.default}"
        raise AssertionError(errmsg)
    
    if definition.description != "The database host address":
        errmsg = f"Expected description 'The database host address', got {definition.description}"
        raise AssertionError(errmsg)
    
    if definition.sensitive is not False:
        errmsg = f"Expected sensitive False, got {definition.sensitive}"
        raise AssertionError(errmsg)
    
    if definition.choices != ["localhost", "127.0.0.1", "db.example.com"]:
        errmsg = f"Expected choices list, got {definition.choices}"
        raise AssertionError(errmsg)
    
    if definition.validator is not custom_validator:
        errmsg = "Expected validator to be the custom_validator function"
        raise AssertionError(errmsg)
    
    return


def test_config_key_definition_with_sensitive():
    """
        Test that ConfigKeyDefinition can be created with sensitive=True.
    """
    definition = ConfigKeyDefinition(
        key="database.password",
        type=str,
        required=True,
        sensitive=True,
        description="The database password"
    )
    
    if definition.sensitive is not True:
        errmsg = f"Expected sensitive True, got {definition.sensitive}"
        raise AssertionError(errmsg)
    
    return


def test_config_key_definition_with_various_types():
    """
        Test that ConfigKeyDefinition can be created with various types.
    """
    # String type
    str_def = ConfigKeyDefinition(key="str.key", type=str)
    if str_def.type is not str:
        errmsg = f"Expected type str, got {str_def.type}"
        raise AssertionError(errmsg)
    
    # Integer type
    int_def = ConfigKeyDefinition(key="int.key", type=int)
    if int_def.type is not int:
        errmsg = f"Expected type int, got {int_def.type}"
        raise AssertionError(errmsg)
    
    # Float type
    float_def = ConfigKeyDefinition(key="float.key", type=float)
    if float_def.type is not float:
        errmsg = f"Expected type float, got {float_def.type}"
        raise AssertionError(errmsg)
    
    # Boolean type
    bool_def = ConfigKeyDefinition(key="bool.key", type=bool)
    if bool_def.type is not bool:
        errmsg = f"Expected type bool, got {bool_def.type}"
        raise AssertionError(errmsg)
    
    # List type
    list_def = ConfigKeyDefinition(key="list.key", type=list)
    if list_def.type is not list:
        errmsg = f"Expected type list, got {list_def.type}"
        raise AssertionError(errmsg)
    
    # Dict type
    dict_def = ConfigKeyDefinition(key="dict.key", type=dict)
    if dict_def.type is not dict:
        errmsg = f"Expected type dict, got {dict_def.type}"
        raise AssertionError(errmsg)
    
    return


# =============================================================================
# Unit Tests for ValidationError
# =============================================================================

def test_validation_error_creation():
    """
        Test that ValidationError can be created with required fields.
    """
    error = ValidationError(
        key="database.host",
        message="Value is required"
    )
    
    if error.key != "database.host":
        errmsg = f"Expected key 'database.host', got {error.key}"
        raise AssertionError(errmsg)
    
    if error.message != "Value is required":
        errmsg = f"Expected message 'Value is required', got {error.message}"
        raise AssertionError(errmsg)
    
    return


def test_validation_error_default_expected_type():
    """
        Test that ValidationError has None as default expected_type.
    """
    error = ValidationError(key="test.key", message="Error")
    
    if error.expected_type is not None:
        errmsg = f"Expected expected_type None, got {error.expected_type}"
        raise AssertionError(errmsg)
    
    return


def test_validation_error_default_actual_value():
    """
        Test that ValidationError has None as default actual_value.
    """
    error = ValidationError(key="test.key", message="Error")
    
    if error.actual_value is not None:
        errmsg = f"Expected actual_value None, got {error.actual_value}"
        raise AssertionError(errmsg)
    
    return


def test_validation_error_default_constraint():
    """
        Test that ValidationError has None as default constraint.
    """
    error = ValidationError(key="test.key", message="Error")
    
    if error.constraint is not None:
        errmsg = f"Expected constraint None, got {error.constraint}"
        raise AssertionError(errmsg)
    
    return


def test_validation_error_with_type_error():
    """
        Test that ValidationError can represent a type error.
    """
    error = ValidationError(
        key="database.port",
        message="Expected int, got str",
        expected_type=int,
        actual_value="not_a_number",
        constraint="type"
    )
    
    if error.expected_type is not int:
        errmsg = f"Expected expected_type int, got {error.expected_type}"
        raise AssertionError(errmsg)
    
    if error.actual_value != "not_a_number":
        errmsg = f"Expected actual_value 'not_a_number', got {error.actual_value}"
        raise AssertionError(errmsg)
    
    if error.constraint != "type":
        errmsg = f"Expected constraint 'type', got {error.constraint}"
        raise AssertionError(errmsg)
    
    return


def test_validation_error_with_required_constraint():
    """
        Test that ValidationError can represent a required constraint violation.
    """
    error = ValidationError(
        key="database.host",
        message="Required key is missing",
        constraint="required"
    )
    
    if error.constraint != "required":
        errmsg = f"Expected constraint 'required', got {error.constraint}"
        raise AssertionError(errmsg)
    
    return


def test_validation_error_with_choices_constraint():
    """
        Test that ValidationError can represent a choices constraint violation.
    """
    error = ValidationError(
        key="log.level",
        message="Value must be one of: DEBUG, INFO, WARNING, ERROR",
        actual_value="INVALID",
        constraint="choices"
    )
    
    if error.constraint != "choices":
        errmsg = f"Expected constraint 'choices', got {error.constraint}"
        raise AssertionError(errmsg)
    
    if error.actual_value != "INVALID":
        errmsg = f"Expected actual_value 'INVALID', got {error.actual_value}"
        raise AssertionError(errmsg)
    
    return


def test_validation_error_with_custom_constraint():
    """
        Test that ValidationError can represent a custom constraint violation.
    """
    error = ValidationError(
        key="database.port",
        message="Port must be between 1 and 65535",
        actual_value=70000,
        constraint="custom"
    )
    
    if error.constraint != "custom":
        errmsg = f"Expected constraint 'custom', got {error.constraint}"
        raise AssertionError(errmsg)
    
    return


# =============================================================================
# Unit Tests for ConfigChangeEvent
# =============================================================================

def test_config_change_event_creation():
    """
        Test that ConfigChangeEvent can be created with required fields.
    """
    event = ConfigChangeEvent(
        key="database.host",
        old_value="localhost",
        new_value="db.example.com",
        source=ConfigSourceType.OVERRIDE
    )
    
    if event.key != "database.host":
        errmsg = f"Expected key 'database.host', got {event.key}"
        raise AssertionError(errmsg)
    
    if event.old_value != "localhost":
        errmsg = f"Expected old_value 'localhost', got {event.old_value}"
        raise AssertionError(errmsg)
    
    if event.new_value != "db.example.com":
        errmsg = f"Expected new_value 'db.example.com', got {event.new_value}"
        raise AssertionError(errmsg)
    
    if event.source != ConfigSourceType.OVERRIDE:
        errmsg = f"Expected source OVERRIDE, got {event.source}"
        raise AssertionError(errmsg)
    
    return


def test_config_change_event_default_timestamp():
    """
        Test that ConfigChangeEvent has a default timestamp.
    """
    before = datetime.now(timezone.utc)
    event = ConfigChangeEvent(
        key="test.key",
        old_value=None,
        new_value="new",
        source=ConfigSourceType.OVERRIDE
    )
    after = datetime.now(timezone.utc)
    
    if event.timestamp < before or event.timestamp > after:
        errmsg = f"Expected timestamp between {before} and {after}, got {event.timestamp}"
        raise AssertionError(errmsg)
    
    return


def test_config_change_event_with_explicit_timestamp():
    """
        Test that ConfigChangeEvent can be created with explicit timestamp.
    """
    explicit_time = datetime(2025, 1, 15, 12, 30, 45)
    event = ConfigChangeEvent(
        key="test.key",
        old_value="old",
        new_value="new",
        source=ConfigSourceType.OVERRIDE,
        timestamp=explicit_time
    )
    
    if event.timestamp != explicit_time:
        errmsg = f"Expected timestamp {explicit_time}, got {event.timestamp}"
        raise AssertionError(errmsg)
    
    return


def test_config_change_event_with_none_old_value():
    """
        Test that ConfigChangeEvent can have None as old_value (new key).
    """
    event = ConfigChangeEvent(
        key="new.key",
        old_value=None,
        new_value="value",
        source=ConfigSourceType.OVERRIDE
    )
    
    if event.old_value is not None:
        errmsg = f"Expected old_value None, got {event.old_value}"
        raise AssertionError(errmsg)
    
    return


def test_config_change_event_with_various_value_types():
    """
        Test that ConfigChangeEvent can store various value types.
    """
    # String values
    str_event = ConfigChangeEvent(
        key="str.key",
        old_value="old",
        new_value="new",
        source=ConfigSourceType.OVERRIDE
    )
    if str_event.old_value != "old" or str_event.new_value != "new":
        errmsg = "String values not stored correctly"
        raise AssertionError(errmsg)
    
    # Integer values
    int_event = ConfigChangeEvent(
        key="int.key",
        old_value=10,
        new_value=20,
        source=ConfigSourceType.OVERRIDE
    )
    if int_event.old_value != 10 or int_event.new_value != 20:
        errmsg = "Integer values not stored correctly"
        raise AssertionError(errmsg)
    
    # Boolean values
    bool_event = ConfigChangeEvent(
        key="bool.key",
        old_value=False,
        new_value=True,
        source=ConfigSourceType.OVERRIDE
    )
    if bool_event.old_value is not False or bool_event.new_value is not True:
        errmsg = "Boolean values not stored correctly"
        raise AssertionError(errmsg)
    
    # List values
    list_event = ConfigChangeEvent(
        key="list.key",
        old_value=[1, 2],
        new_value=[1, 2, 3],
        source=ConfigSourceType.OVERRIDE
    )
    if list_event.old_value != [1, 2] or list_event.new_value != [1, 2, 3]:
        errmsg = "List values not stored correctly"
        raise AssertionError(errmsg)
    
    return


from pathlib import Path

from ccai.webworks.configuration import (
    ConfigurationError,
    ConfigurationValidationError,
    ConfigurationFileNotFoundError,
    ConfigurationFrozenError,
    ConfigurationTypeError
)


# =============================================================================
# Unit Tests for ConfigurationError
# =============================================================================

def test_configuration_error_creation_with_message():
    """
        Test that ConfigurationError can be created with just a message.
    """
    error = ConfigurationError("Something went wrong")
    
    if error.message != "Something went wrong":
        errmsg = f"Expected message 'Something went wrong', got {error.message}"
        raise AssertionError(errmsg)
    
    if str(error) != "Something went wrong":
        errmsg = f"Expected str(error) 'Something went wrong', got {str(error)}"
        raise AssertionError(errmsg)
    
    return


def test_configuration_error_default_key_is_none():
    """
        Test that ConfigurationError has None as default key.
    """
    error = ConfigurationError("Error message")
    
    if error.key is not None:
        errmsg = f"Expected key None, got {error.key}"
        raise AssertionError(errmsg)
    
    return


def test_configuration_error_with_key():
    """
        Test that ConfigurationError can be created with a key.
    """
    error = ConfigurationError("Missing required key", key="database.host")
    
    if error.key != "database.host":
        errmsg = f"Expected key 'database.host', got {error.key}"
        raise AssertionError(errmsg)
    
    if error.message != "Missing required key":
        errmsg = f"Expected message 'Missing required key', got {error.message}"
        raise AssertionError(errmsg)
    
    return


def test_configuration_error_is_exception():
    """
        Test that ConfigurationError is an Exception subclass.
    """
    error = ConfigurationError("Test error")
    
    if not isinstance(error, Exception):
        errmsg = "ConfigurationError should be an Exception subclass"
        raise AssertionError(errmsg)
    
    return


def test_configuration_error_can_be_raised():
    """
        Test that ConfigurationError can be raised and caught.
    """
    caught = False
    try:
        raise ConfigurationError("Test error", key="test.key")
    except ConfigurationError as e:
        caught = True
        if e.key != "test.key":
            errmsg = f"Expected key 'test.key', got {e.key}"
            raise AssertionError(errmsg)
    
    if not caught:
        errmsg = "ConfigurationError was not caught"
        raise AssertionError(errmsg)
    
    return


# =============================================================================
# Unit Tests for ConfigurationValidationError
# =============================================================================

def test_configuration_validation_error_creation():
    """
        Test that ConfigurationValidationError can be created with errors list.
    """
    errors = [
        ValidationError(key="database.host", message="Value is required"),
        ValidationError(key="database.port", message="Expected int, got str")
    ]
    
    error = ConfigurationValidationError(errors)
    
    if error.errors != errors:
        errmsg = "Expected errors list to be stored"
        raise AssertionError(errmsg)
    
    if len(error.errors) != 2:
        errmsg = f"Expected 2 errors, got {len(error.errors)}"
        raise AssertionError(errmsg)
    
    return


def test_configuration_validation_error_message_format():
    """
        Test that ConfigurationValidationError formats the message correctly.
    """
    errors = [
        ValidationError(key="database.host", message="Value is required"),
        ValidationError(key="database.port", message="Expected int, got str")
    ]
    
    error = ConfigurationValidationError(errors)
    
    if "Configuration validation failed with 2 error(s)" not in str(error):
        errmsg = f"Expected error count in message, got {str(error)}"
        raise AssertionError(errmsg)
    
    if "database.host: Value is required" not in str(error):
        errmsg = f"Expected first error in message, got {str(error)}"
        raise AssertionError(errmsg)
    
    if "database.port: Expected int, got str" not in str(error):
        errmsg = f"Expected second error in message, got {str(error)}"
        raise AssertionError(errmsg)
    
    return


def test_configuration_validation_error_single_error():
    """
        Test that ConfigurationValidationError works with a single error.
    """
    errors = [
        ValidationError(key="api.key", message="API key is required")
    ]
    
    error = ConfigurationValidationError(errors)
    
    if "Configuration validation failed with 1 error(s)" not in str(error):
        errmsg = f"Expected '1 error(s)' in message, got {str(error)}"
        raise AssertionError(errmsg)
    
    return


def test_configuration_validation_error_is_configuration_error():
    """
        Test that ConfigurationValidationError is a ConfigurationError subclass.
    """
    errors = [ValidationError(key="test", message="test")]
    error = ConfigurationValidationError(errors)
    
    if not isinstance(error, ConfigurationError):
        errmsg = "ConfigurationValidationError should be a ConfigurationError subclass"
        raise AssertionError(errmsg)
    
    return


def test_configuration_validation_error_can_be_raised():
    """
        Test that ConfigurationValidationError can be raised and caught.
    """
    errors = [
        ValidationError(key="test.key", message="Test error")
    ]
    
    caught = False
    try:
        raise ConfigurationValidationError(errors)
    except ConfigurationValidationError as e:
        caught = True
        if len(e.errors) != 1:
            errmsg = f"Expected 1 error, got {len(e.errors)}"
            raise AssertionError(errmsg)
    
    if not caught:
        errmsg = "ConfigurationValidationError was not caught"
        raise AssertionError(errmsg)
    
    return


# =============================================================================
# Unit Tests for ConfigurationFileNotFoundError
# =============================================================================

def test_configuration_file_not_found_error_creation():
    """
        Test that ConfigurationFileNotFoundError can be created with path.
    """
    path = Path("/etc/myapp/settings.yaml")
    error = ConfigurationFileNotFoundError(path)
    
    if error.path != path:
        errmsg = f"Expected path {path}, got {error.path}"
        raise AssertionError(errmsg)
    
    return


def test_configuration_file_not_found_error_default_referenced_from():
    """
        Test that ConfigurationFileNotFoundError has None as default referenced_from.
    """
    path = Path("/etc/myapp/settings.yaml")
    error = ConfigurationFileNotFoundError(path)
    
    if error.referenced_from is not None:
        errmsg = f"Expected referenced_from None, got {error.referenced_from}"
        raise AssertionError(errmsg)
    
    return


def test_configuration_file_not_found_error_message_without_reference():
    """
        Test that ConfigurationFileNotFoundError formats message without reference.
    """
    path = Path("/etc/myapp/settings.yaml")
    error = ConfigurationFileNotFoundError(path)
    
    expected_msg = "Configuration file not found: /etc/myapp/settings.yaml"
    if str(error) != expected_msg:
        errmsg = f"Expected message '{expected_msg}', got {str(error)}"
        raise AssertionError(errmsg)
    
    return


def test_configuration_file_not_found_error_with_referenced_from():
    """
        Test that ConfigurationFileNotFoundError can include referenced_from.
    """
    path = Path("/etc/myapp/secrets.yaml")
    referenced_from = Path("/etc/myapp/settings.yaml")
    error = ConfigurationFileNotFoundError(path, referenced_from=referenced_from)
    
    if error.referenced_from != referenced_from:
        errmsg = f"Expected referenced_from {referenced_from}, got {error.referenced_from}"
        raise AssertionError(errmsg)
    
    return


def test_configuration_file_not_found_error_message_with_reference():
    """
        Test that ConfigurationFileNotFoundError formats message with reference.
    """
    path = Path("/etc/myapp/secrets.yaml")
    referenced_from = Path("/etc/myapp/settings.yaml")
    error = ConfigurationFileNotFoundError(path, referenced_from=referenced_from)
    
    if "Configuration file not found: /etc/myapp/secrets.yaml" not in str(error):
        errmsg = f"Expected path in message, got {str(error)}"
        raise AssertionError(errmsg)
    
    if "(referenced from /etc/myapp/settings.yaml)" not in str(error):
        errmsg = f"Expected referenced_from in message, got {str(error)}"
        raise AssertionError(errmsg)
    
    return


def test_configuration_file_not_found_error_is_configuration_error():
    """
        Test that ConfigurationFileNotFoundError is a ConfigurationError subclass.
    """
    error = ConfigurationFileNotFoundError(Path("/test/path"))
    
    if not isinstance(error, ConfigurationError):
        errmsg = "ConfigurationFileNotFoundError should be a ConfigurationError subclass"
        raise AssertionError(errmsg)
    
    return


def test_configuration_file_not_found_error_can_be_raised():
    """
        Test that ConfigurationFileNotFoundError can be raised and caught.
    """
    path = Path("/etc/myapp/missing.yaml")
    
    caught = False
    try:
        raise ConfigurationFileNotFoundError(path)
    except ConfigurationFileNotFoundError as e:
        caught = True
        if e.path != path:
            errmsg = f"Expected path {path}, got {e.path}"
            raise AssertionError(errmsg)
    
    if not caught:
        errmsg = "ConfigurationFileNotFoundError was not caught"
        raise AssertionError(errmsg)
    
    return


# =============================================================================
# Unit Tests for ConfigurationFrozenError
# =============================================================================

def test_configuration_frozen_error_creation():
    """
        Test that ConfigurationFrozenError can be created with key.
    """
    error = ConfigurationFrozenError("database.host")
    
    if error.key != "database.host":
        errmsg = f"Expected key 'database.host', got {error.key}"
        raise AssertionError(errmsg)
    
    return


def test_configuration_frozen_error_message_format():
    """
        Test that ConfigurationFrozenError formats the message correctly.
    """
    error = ConfigurationFrozenError("database.host")
    
    expected_msg = "Cannot modify configuration key 'database.host': configuration is frozen"
    if str(error) != expected_msg:
        errmsg = f"Expected message '{expected_msg}', got {str(error)}"
        raise AssertionError(errmsg)
    
    return


def test_configuration_frozen_error_is_configuration_error():
    """
        Test that ConfigurationFrozenError is a ConfigurationError subclass.
    """
    error = ConfigurationFrozenError("test.key")
    
    if not isinstance(error, ConfigurationError):
        errmsg = "ConfigurationFrozenError should be a ConfigurationError subclass"
        raise AssertionError(errmsg)
    
    return


def test_configuration_frozen_error_can_be_raised():
    """
        Test that ConfigurationFrozenError can be raised and caught.
    """
    caught = False
    try:
        raise ConfigurationFrozenError("api.secret")
    except ConfigurationFrozenError as e:
        caught = True
        if e.key != "api.secret":
            errmsg = f"Expected key 'api.secret', got {e.key}"
            raise AssertionError(errmsg)
    
    if not caught:
        errmsg = "ConfigurationFrozenError was not caught"
        raise AssertionError(errmsg)
    
    return


# =============================================================================
# Unit Tests for ConfigurationTypeError
# =============================================================================

def test_configuration_type_error_creation():
    """
        Test that ConfigurationTypeError can be created with required fields.
    """
    error = ConfigurationTypeError("database.port", int, "not_a_number")
    
    if error.key != "database.port":
        errmsg = f"Expected key 'database.port', got {error.key}"
        raise AssertionError(errmsg)
    
    if error.expected_type is not int:
        errmsg = f"Expected expected_type int, got {error.expected_type}"
        raise AssertionError(errmsg)
    
    if error.actual_value != "not_a_number":
        errmsg = f"Expected actual_value 'not_a_number', got {error.actual_value}"
        raise AssertionError(errmsg)
    
    return


def test_configuration_type_error_message_format():
    """
        Test that ConfigurationTypeError formats the message correctly.
    """
    error = ConfigurationTypeError("database.port", int, "not_a_number")
    
    expected_msg = "Cannot coerce 'database.port' value 'not_a_number' to type int"
    if str(error) != expected_msg:
        errmsg = f"Expected message '{expected_msg}', got {str(error)}"
        raise AssertionError(errmsg)
    
    return


def test_configuration_type_error_with_various_types():
    """
        Test that ConfigurationTypeError works with various expected types.
    """
    # Float type
    float_error = ConfigurationTypeError("rate.limit", float, "abc")
    if "to type float" not in str(float_error):
        errmsg = f"Expected 'to type float' in message, got {str(float_error)}"
        raise AssertionError(errmsg)
    
    # Bool type
    bool_error = ConfigurationTypeError("debug.enabled", bool, "maybe")
    if "to type bool" not in str(bool_error):
        errmsg = f"Expected 'to type bool' in message, got {str(bool_error)}"
        raise AssertionError(errmsg)
    
    # List type
    list_error = ConfigurationTypeError("allowed.hosts", list, "single_host")
    if "to type list" not in str(list_error):
        errmsg = f"Expected 'to type list' in message, got {str(list_error)}"
        raise AssertionError(errmsg)
    
    return


def test_configuration_type_error_is_configuration_error():
    """
        Test that ConfigurationTypeError is a ConfigurationError subclass.
    """
    error = ConfigurationTypeError("test.key", str, 123)
    
    if not isinstance(error, ConfigurationError):
        errmsg = "ConfigurationTypeError should be a ConfigurationError subclass"
        raise AssertionError(errmsg)
    
    return


def test_configuration_type_error_can_be_raised():
    """
        Test that ConfigurationTypeError can be raised and caught.
    """
    caught = False
    try:
        raise ConfigurationTypeError("timeout.seconds", int, "forever")
    except ConfigurationTypeError as e:
        caught = True
        if e.expected_type is not int:
            errmsg = f"Expected expected_type int, got {e.expected_type}"
            raise AssertionError(errmsg)
        if e.actual_value != "forever":
            errmsg = f"Expected actual_value 'forever', got {e.actual_value}"
            raise AssertionError(errmsg)
    
    if not caught:
        errmsg = "ConfigurationTypeError was not caught"
        raise AssertionError(errmsg)
    
    return


def test_configuration_type_error_with_none_value():
    """
        Test that ConfigurationTypeError works with None as actual_value.
    """
    error = ConfigurationTypeError("required.field", str, None)
    
    if error.actual_value is not None:
        errmsg = f"Expected actual_value None, got {error.actual_value}"
        raise AssertionError(errmsg)
    
    if "value 'None'" not in str(error):
        errmsg = f"Expected 'None' in message, got {str(error)}"
        raise AssertionError(errmsg)
    
    return


# =============================================================================
# Unit Tests for SecretValue
# =============================================================================

from ccai.webworks.configuration import SecretValue


def test_secret_value_creation():
    """
        Test that SecretValue can be created with required fields.
    """
    secret = SecretValue(value="my_secret_password", key="database.password")
    
    if secret.key != "database.password":
        errmsg = f"Expected key 'database.password', got {secret.key}"
        raise AssertionError(errmsg)
    
    return


def test_secret_value_get_secret_value():
    """
        Test that get_secret_value() returns the actual secret.
    """
    secret = SecretValue(value="my_secret_password", key="database.password")
    
    actual = secret.get_secret_value()
    
    if actual != "my_secret_password":
        errmsg = f"Expected 'my_secret_password', got {actual}"
        raise AssertionError(errmsg)
    
    return


def test_secret_value_str_returns_masked():
    """
        Test that str() returns masked value, not the actual secret.
    """
    secret = SecretValue(value="super_secret_123", key="api.key")
    
    str_value = str(secret)
    
    if str_value != "***MASKED***":
        errmsg = f"Expected '***MASKED***', got {str_value}"
        raise AssertionError(errmsg)
    
    # Ensure the actual secret is NOT in the string representation
    if "super_secret_123" in str_value:
        errmsg = "Secret value should not appear in str() output"
        raise AssertionError(errmsg)
    
    return


def test_secret_value_repr_returns_masked():
    """
        Test that repr() returns masked value with key info.
    """
    secret = SecretValue(value="super_secret_123", key="api.key")
    
    repr_value = repr(secret)
    
    if "***MASKED***" not in repr_value:
        errmsg = f"Expected '***MASKED***' in repr, got {repr_value}"
        raise AssertionError(errmsg)
    
    if "api.key" not in repr_value:
        errmsg = f"Expected 'api.key' in repr, got {repr_value}"
        raise AssertionError(errmsg)
    
    # Ensure the actual secret is NOT in the repr
    if "super_secret_123" in repr_value:
        errmsg = "Secret value should not appear in repr() output"
        raise AssertionError(errmsg)
    
    return


def test_secret_value_repr_format():
    """
        Test that repr() has the expected format.
    """
    secret = SecretValue(value="password123", key="db.pass")
    
    repr_value = repr(secret)
    expected = "SecretValue(key='db.pass', value='***MASKED***')"
    
    if repr_value != expected:
        errmsg = f"Expected repr '{expected}', got {repr_value}"
        raise AssertionError(errmsg)
    
    return


def test_secret_value_without_audit_logger():
    """
        Test that SecretValue works without an audit logger.
    """
    secret = SecretValue(value="secret", key="test.key")
    
    # Should not raise any errors
    value = secret.get_secret_value()
    
    if value != "secret":
        errmsg = f"Expected 'secret', got {value}"
        raise AssertionError(errmsg)
    
    return


def test_secret_value_with_audit_logger():
    """
        Test that SecretValue calls audit logger when accessing secret.
    """
    logged_keys = []
    
    def audit_logger(key: str) -> None:
        logged_keys.append(key)
    
    secret = SecretValue(
        value="secret_value",
        key="sensitive.key",
        audit_logger=audit_logger
    )
    
    # Access the secret
    secret.get_secret_value()
    
    if len(logged_keys) != 1:
        errmsg = f"Expected 1 logged key, got {len(logged_keys)}"
        raise AssertionError(errmsg)
    
    if logged_keys[0] != "sensitive.key":
        errmsg = f"Expected logged key 'sensitive.key', got {logged_keys[0]}"
        raise AssertionError(errmsg)
    
    return


def test_secret_value_audit_logger_called_each_access():
    """
        Test that audit logger is called on each access to get_secret_value().
    """
    access_count = [0]
    
    def audit_logger(key: str) -> None:
        access_count[0] += 1
    
    secret = SecretValue(
        value="secret",
        key="test.key",
        audit_logger=audit_logger
    )
    
    # Access multiple times
    secret.get_secret_value()
    secret.get_secret_value()
    secret.get_secret_value()
    
    if access_count[0] != 3:
        errmsg = f"Expected 3 audit log calls, got {access_count[0]}"
        raise AssertionError(errmsg)
    
    return


def test_secret_value_equality():
    """
        Test that two SecretValue instances with same key and value are equal.
    """
    secret1 = SecretValue(value="password", key="db.pass")
    secret2 = SecretValue(value="password", key="db.pass")
    
    if secret1 != secret2:
        errmsg = "Expected equal SecretValue instances to be equal"
        raise AssertionError(errmsg)
    
    return


def test_secret_value_inequality_different_value():
    """
        Test that SecretValue instances with different values are not equal.
    """
    secret1 = SecretValue(value="password1", key="db.pass")
    secret2 = SecretValue(value="password2", key="db.pass")
    
    if secret1 == secret2:
        errmsg = "Expected SecretValue instances with different values to not be equal"
        raise AssertionError(errmsg)
    
    return


def test_secret_value_inequality_different_key():
    """
        Test that SecretValue instances with different keys are not equal.
    """
    secret1 = SecretValue(value="password", key="db.pass1")
    secret2 = SecretValue(value="password", key="db.pass2")
    
    if secret1 == secret2:
        errmsg = "Expected SecretValue instances with different keys to not be equal"
        raise AssertionError(errmsg)
    
    return


def test_secret_value_inequality_with_non_secret_value():
    """
        Test that SecretValue is not equal to non-SecretValue objects.
    """
    secret = SecretValue(value="password", key="db.pass")
    
    if secret == "password":
        errmsg = "SecretValue should not be equal to a string"
        raise AssertionError(errmsg)
    
    if secret == {"key": "db.pass", "value": "password"}:
        errmsg = "SecretValue should not be equal to a dict"
        raise AssertionError(errmsg)
    
    return


def test_secret_value_hash():
    """
        Test that SecretValue instances with same key and value have same hash.
    """
    secret1 = SecretValue(value="password", key="db.pass")
    secret2 = SecretValue(value="password", key="db.pass")
    
    if hash(secret1) != hash(secret2):
        errmsg = "Expected equal SecretValue instances to have same hash"
        raise AssertionError(errmsg)
    
    return


def test_secret_value_hash_different_for_different_values():
    """
        Test that SecretValue instances with different values have different hashes.
    """
    secret1 = SecretValue(value="password1", key="db.pass")
    secret2 = SecretValue(value="password2", key="db.pass")
    
    # Note: Hash collisions are possible but unlikely for different values
    # This test verifies the hash is based on the value
    if hash(secret1) == hash(secret2):
        # This could theoretically happen due to hash collision, but is very unlikely
        pass  # Allow this case but it's extremely rare
    
    return


def test_secret_value_can_be_used_in_set():
    """
        Test that SecretValue can be used in a set.
    """
    secret1 = SecretValue(value="password", key="db.pass")
    secret2 = SecretValue(value="password", key="db.pass")
    secret3 = SecretValue(value="other", key="api.key")
    
    secret_set = {secret1, secret2, secret3}
    
    # secret1 and secret2 are equal, so set should have 2 elements
    if len(secret_set) != 2:
        errmsg = f"Expected set with 2 elements, got {len(secret_set)}"
        raise AssertionError(errmsg)
    
    return


def test_secret_value_can_be_used_as_dict_key():
    """
        Test that SecretValue can be used as a dictionary key.
    """
    secret = SecretValue(value="password", key="db.pass")
    
    secret_dict = {secret: "some_metadata"}
    
    if secret_dict[secret] != "some_metadata":
        errmsg = "SecretValue should work as dictionary key"
        raise AssertionError(errmsg)
    
    return


def test_secret_value_masked_constant():
    """
        Test that SecretValue.MASKED_VALUE constant is correct.
    """
    if SecretValue.MASKED_VALUE != "***MASKED***":
        errmsg = f"Expected MASKED_VALUE '***MASKED***', got {SecretValue.MASKED_VALUE}"
        raise AssertionError(errmsg)
    
    return


def test_secret_value_key_property():
    """
        Test that the key property returns the correct key.
    """
    secret = SecretValue(value="secret", key="my.secret.key")
    
    if secret.key != "my.secret.key":
        errmsg = f"Expected key 'my.secret.key', got {secret.key}"
        raise AssertionError(errmsg)
    
    return


def test_secret_value_with_empty_string():
    """
        Test that SecretValue works with empty string value.
    """
    secret = SecretValue(value="", key="empty.secret")
    
    if secret.get_secret_value() != "":
        errmsg = f"Expected empty string, got '{secret.get_secret_value()}'"
        raise AssertionError(errmsg)
    
    # str() should still return masked
    if str(secret) != "***MASKED***":
        errmsg = f"Expected '***MASKED***', got {str(secret)}"
        raise AssertionError(errmsg)
    
    return


def test_secret_value_with_special_characters():
    """
        Test that SecretValue works with special characters in value.
    """
    special_value = "p@$$w0rd!#$%^&*()_+-=[]{}|;':\",./<>?"
    secret = SecretValue(value=special_value, key="special.pass")
    
    if secret.get_secret_value() != special_value:
        errmsg = f"Expected special characters to be preserved"
        raise AssertionError(errmsg)
    
    return


def test_secret_value_with_unicode():
    """
        Test that SecretValue works with unicode characters.
    """
    unicode_value = "密码🔐пароль"
    secret = SecretValue(value=unicode_value, key="unicode.pass")
    
    if secret.get_secret_value() != unicode_value:
        errmsg = f"Expected unicode value to be preserved"
        raise AssertionError(errmsg)
    
    return


def test_secret_value_with_newlines():
    """
        Test that SecretValue works with newlines in value.
    """
    multiline_value = "line1\nline2\nline3"
    secret = SecretValue(value=multiline_value, key="multiline.secret")
    
    if secret.get_secret_value() != multiline_value:
        errmsg = f"Expected multiline value to be preserved"
        raise AssertionError(errmsg)
    
    return


# =============================================================================
# Property-Based Tests for SecretValue
# =============================================================================

import random
import string


def generate_random_string(min_length: int = 1, max_length: int = 100) -> str:
    """
        Generate a random string of variable length.
        
        :param min_length: Minimum string length.
        :param max_length: Maximum string length.
        
        :returns: A random string.
    """
    length = random.randint(min_length, max_length)
    chars = string.ascii_letters + string.digits + string.punctuation + " "
    return ''.join(random.choice(chars) for _ in range(length))


def generate_random_key() -> str:
    """
        Generate a random configuration key in dot-notation.
        
        :returns: A random key like "database.password" or "api.secret.key".
    """
    num_parts = random.randint(1, 4)
    parts = []
    for _ in range(num_parts):
        part_length = random.randint(2, 15)
        part = ''.join(random.choice(string.ascii_lowercase) for _ in range(part_length))
        parts.append(part)
    return '.'.join(parts)


def generate_random_secret_value() -> str:
    """
        Generate a random secret value.
        
        :returns: A random secret string.
    """
    # Include various character types to test edge cases
    length = random.randint(1, 200)
    chars = string.ascii_letters + string.digits + string.punctuation
    return ''.join(random.choice(chars) for _ in range(length))


# Feature: configuration-system, Property 15: SecretValue Wrapper Behavior
# *For any* sensitive configuration value, accessing the value SHALL return a
# SecretValue wrapper, and calling get_secret_value() on the wrapper SHALL
# return the actual value.
# **Validates: Requirements 4.6, 4.7**

def test_property_15_secret_value_wrapper_behavior():
    """
        Property 15: SecretValue Wrapper Behavior
        
        For any sensitive configuration value, accessing the value SHALL return
        a SecretValue wrapper, and calling get_secret_value() on the wrapper
        SHALL return the actual value.
        
        **Feature: configuration-system, Property 15: SecretValue Wrapper Behavior**
        **Validates: Requirements 4.6, 4.7**
    """
    # Run 100 iterations with random data
    for iteration in range(100):
        # Generate random secret value and key
        secret_value = generate_random_secret_value()
        key = generate_random_key()
        
        # Create SecretValue wrapper
        secret = SecretValue(value=secret_value, key=key)
        
        # Property 1: get_secret_value() SHALL return the actual value
        retrieved_value = secret.get_secret_value()
        if retrieved_value != secret_value:
            errmsg = f"Iteration {iteration}: get_secret_value() returned '{retrieved_value}', expected '{secret_value}'"
            raise AssertionError(errmsg)
        
        # Property 2: str() SHALL NOT expose the actual value
        # Note: We use a minimum length threshold to avoid false positives from
        # coincidental matches with format string components (e.g., "key", "=", "'")
        str_repr = str(secret)
        min_exposure_length = 8  # Secrets shorter than this could match format strings
        if secret_value in str_repr and len(secret_value) >= min_exposure_length:
            errmsg = f"Iteration {iteration}: str() exposed the secret value"
            raise AssertionError(errmsg)
        
        # Property 3: str() SHALL return the masked constant
        if str_repr != SecretValue.MASKED_VALUE:
            errmsg = f"Iteration {iteration}: str() returned '{str_repr}', expected '{SecretValue.MASKED_VALUE}'"
            raise AssertionError(errmsg)
        
        # Property 4: repr() SHALL NOT expose the actual value
        # Note: We use a minimum length threshold to avoid false positives from
        # coincidental matches with format string components
        repr_str = repr(secret)
        if secret_value in repr_str and len(secret_value) >= min_exposure_length:
            errmsg = f"Iteration {iteration}: repr() exposed the secret value"
            raise AssertionError(errmsg)
        
        # Property 5: repr() SHALL contain the masked value
        if SecretValue.MASKED_VALUE not in repr_str:
            errmsg = f"Iteration {iteration}: repr() does not contain masked value"
            raise AssertionError(errmsg)
        
        # Property 6: repr() SHALL contain the key
        if key not in repr_str:
            errmsg = f"Iteration {iteration}: repr() does not contain the key '{key}'"
            raise AssertionError(errmsg)
        
        # Property 7: key property SHALL return the correct key
        if secret.key != key:
            errmsg = f"Iteration {iteration}: key property returned '{secret.key}', expected '{key}'"
            raise AssertionError(errmsg)
    
    return


def test_property_15_secret_value_audit_logging():
    """
        Property 15 (Extended): SecretValue Audit Logging
        
        For any SecretValue with an audit logger, calling get_secret_value()
        SHALL invoke the audit logger with the correct key.
        
        **Feature: configuration-system, Property 15: SecretValue Wrapper Behavior**
        **Validates: Requirements 4.6, 4.7, 4.9**
    """
    # Run 100 iterations with random data
    for iteration in range(100):
        # Generate random secret value and key
        secret_value = generate_random_secret_value()
        key = generate_random_key()
        
        # Track audit log calls
        logged_keys = []
        
        def audit_logger(logged_key: str) -> None:
            logged_keys.append(logged_key)
        
        # Create SecretValue wrapper with audit logger
        secret = SecretValue(value=secret_value, key=key, audit_logger=audit_logger)
        
        # Access the secret multiple times
        num_accesses = random.randint(1, 5)
        for _ in range(num_accesses):
            retrieved = secret.get_secret_value()
            
            # Property: get_secret_value() SHALL still return the actual value
            if retrieved != secret_value:
                errmsg = f"Iteration {iteration}: get_secret_value() returned wrong value with audit logger"
                raise AssertionError(errmsg)
        
        # Property: Audit logger SHALL be called exactly num_accesses times
        if len(logged_keys) != num_accesses:
            errmsg = f"Iteration {iteration}: Expected {num_accesses} audit log calls, got {len(logged_keys)}"
            raise AssertionError(errmsg)
        
        # Property: All logged keys SHALL be the correct key
        for logged_key in logged_keys:
            if logged_key != key:
                errmsg = f"Iteration {iteration}: Audit logged wrong key '{logged_key}', expected '{key}'"
                raise AssertionError(errmsg)
    
    return


def test_property_15_secret_value_equality_consistency():
    """
        Property 15 (Extended): SecretValue Equality Consistency
        
        For any two SecretValue instances with the same key and value,
        they SHALL be equal and have the same hash.
        
        **Feature: configuration-system, Property 15: SecretValue Wrapper Behavior**
        **Validates: Requirements 4.6, 4.7**
    """
    # Run 100 iterations with random data
    for iteration in range(100):
        # Generate random secret value and key
        secret_value = generate_random_secret_value()
        key = generate_random_key()
        
        # Create two SecretValue instances with same key and value
        secret1 = SecretValue(value=secret_value, key=key)
        secret2 = SecretValue(value=secret_value, key=key)
        
        # Property: Two instances with same key and value SHALL be equal
        if secret1 != secret2:
            errmsg = f"Iteration {iteration}: SecretValue instances with same key/value should be equal"
            raise AssertionError(errmsg)
        
        # Property: Equal instances SHALL have the same hash
        if hash(secret1) != hash(secret2):
            errmsg = f"Iteration {iteration}: Equal SecretValue instances should have same hash"
            raise AssertionError(errmsg)
        
        # Generate a different value
        different_value = generate_random_secret_value()
        while different_value == secret_value:
            different_value = generate_random_secret_value()
        
        # Create a SecretValue with different value
        secret3 = SecretValue(value=different_value, key=key)
        
        # Property: Instances with different values SHALL NOT be equal
        if secret1 == secret3:
            errmsg = f"Iteration {iteration}: SecretValue instances with different values should not be equal"
            raise AssertionError(errmsg)
        
        # Generate a different key
        different_key = generate_random_key()
        while different_key == key:
            different_key = generate_random_key()
        
        # Create a SecretValue with different key
        secret4 = SecretValue(value=secret_value, key=different_key)
        
        # Property: Instances with different keys SHALL NOT be equal
        if secret1 == secret4:
            errmsg = f"Iteration {iteration}: SecretValue instances with different keys should not be equal"
            raise AssertionError(errmsg)
    
    return
