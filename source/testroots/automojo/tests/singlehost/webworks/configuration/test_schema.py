"""
    Tests for the configuration schema module.
    
    This module contains unit tests and property-based tests for the
    ConfigSchema class and type coercion functionality.
"""

import json
import random
import string
from typing import Any, List

from automojo.webworks.configuration import (
    ConfigSchema,
    ConfigKeyDefinition,
    ValidationError,
    coerce_value
)


# =============================================================================
# Helper Functions for Test Data Generation
# =============================================================================

def generate_random_string(min_length: int = 1, max_length: int = 50) -> str:
    """
        Generate a random string of variable length.
        
        :param min_length: Minimum string length.
        :param max_length: Maximum string length.
        
        :returns: A random string.
    """
    length = random.randint(min_length, max_length)
    chars = string.ascii_letters + string.digits + "_"
    return ''.join(random.choice(chars) for _ in range(length))


def generate_random_key() -> str:
    """
        Generate a random configuration key in dot-notation.
        
        :returns: A random key like "database.host" or "api.key".
    """
    num_parts = random.randint(1, 3)
    parts = []
    for _ in range(num_parts):
        part_length = random.randint(2, 10)
        part = ''.join(random.choice(string.ascii_lowercase) for _ in range(part_length))
        parts.append(part)
    return '.'.join(parts)


def generate_random_int() -> int:
    """
        Generate a random integer.
        
        :returns: A random integer.
    """
    return random.randint(-10000, 10000)


def generate_random_float() -> float:
    """
        Generate a random float.
        
        :returns: A random float.
    """
    return random.uniform(-10000.0, 10000.0)


def generate_random_bool() -> bool:
    """
        Generate a random boolean.
        
        :returns: A random boolean.
    """
    return random.choice([True, False])


def generate_random_list() -> list:
    """
        Generate a random list of simple values.
        
        :returns: A random list.
    """
    length = random.randint(0, 10)
    result = []
    for _ in range(length):
        value_type = random.choice(['int', 'str', 'bool'])
        if value_type == 'int':
            result.append(random.randint(-100, 100))
        elif value_type == 'str':
            result.append(generate_random_string(1, 10))
        else:
            result.append(random.choice([True, False]))
    return result


def generate_random_dict() -> dict:
    """
        Generate a random dictionary with simple values.
        
        :returns: A random dictionary.
    """
    num_keys = random.randint(0, 5)
    result = {}
    for _ in range(num_keys):
        key = generate_random_string(2, 8)
        value_type = random.choice(['int', 'str', 'bool'])
        if value_type == 'int':
            result[key] = random.randint(-100, 100)
        elif value_type == 'str':
            result[key] = generate_random_string(1, 10)
        else:
            result[key] = random.choice([True, False])
    return result


# =============================================================================
# Unit Tests for ConfigSchema
# =============================================================================

def test_config_schema_creation():
    """
        Test that ConfigSchema can be created.
    """
    schema = ConfigSchema()
    
    if schema.keys != {}:
        errmsg = f"Expected empty keys dict, got {schema.keys}"
        raise AssertionError(errmsg)
    
    if schema.nested_schemas != {}:
        errmsg = f"Expected empty nested_schemas dict, got {schema.nested_schemas}"
        raise AssertionError(errmsg)
    
    return


def test_config_schema_define_basic():
    """
        Test that ConfigSchema.define() adds a key definition.
    """
    schema = ConfigSchema()
    result = schema.define("database.host", str)
    
    # Should return self for chaining
    if result is not schema:
        errmsg = "define() should return self for method chaining"
        raise AssertionError(errmsg)
    
    # Should have the key defined
    if "database.host" not in schema.keys:
        errmsg = "Key 'database.host' should be in schema.keys"
        raise AssertionError(errmsg)
    
    definition = schema.keys["database.host"]
    if definition.key != "database.host":
        errmsg = f"Expected key 'database.host', got {definition.key}"
        raise AssertionError(errmsg)
    
    if definition.type is not str:
        errmsg = f"Expected type str, got {definition.type}"
        raise AssertionError(errmsg)
    
    return


def test_config_schema_define_with_all_options():
    """
        Test that ConfigSchema.define() accepts all options.
    """
    def custom_validator(value: Any) -> bool:
        return len(value) > 0
    
    schema = ConfigSchema()
    schema.define(
        "database.host",
        str,
        required=True,
        default="localhost",
        description="The database host",
        sensitive=False,
        choices=["localhost", "127.0.0.1"],
        validator=custom_validator
    )
    
    definition = schema.keys["database.host"]
    
    if definition.required is not True:
        errmsg = f"Expected required True, got {definition.required}"
        raise AssertionError(errmsg)
    
    if definition.default != "localhost":
        errmsg = f"Expected default 'localhost', got {definition.default}"
        raise AssertionError(errmsg)
    
    if definition.description != "The database host":
        errmsg = f"Expected description 'The database host', got {definition.description}"
        raise AssertionError(errmsg)
    
    if definition.sensitive is not False:
        errmsg = f"Expected sensitive False, got {definition.sensitive}"
        raise AssertionError(errmsg)
    
    if definition.choices != ["localhost", "127.0.0.1"]:
        errmsg = f"Expected choices list, got {definition.choices}"
        raise AssertionError(errmsg)
    
    if definition.validator is not custom_validator:
        errmsg = "Expected validator to be custom_validator"
        raise AssertionError(errmsg)
    
    return


def test_config_schema_define_chaining():
    """
        Test that ConfigSchema.define() supports method chaining.
    """
    schema = ConfigSchema()
    schema.define("key1", str).define("key2", int).define("key3", bool)
    
    if len(schema.keys) != 3:
        errmsg = f"Expected 3 keys, got {len(schema.keys)}"
        raise AssertionError(errmsg)
    
    if "key1" not in schema.keys:
        errmsg = "key1 should be in schema.keys"
        raise AssertionError(errmsg)
    
    if "key2" not in schema.keys:
        errmsg = "key2 should be in schema.keys"
        raise AssertionError(errmsg)
    
    if "key3" not in schema.keys:
        errmsg = "key3 should be in schema.keys"
        raise AssertionError(errmsg)
    
    return


def test_config_schema_nested():
    """
        Test that ConfigSchema.nested() adds a nested schema.
    """
    parent_schema = ConfigSchema()
    child_schema = ConfigSchema()
    child_schema.define("host", str)
    child_schema.define("port", int)
    
    result = parent_schema.nested("database", child_schema)
    
    # Should return self for chaining
    if result is not parent_schema:
        errmsg = "nested() should return self for method chaining"
        raise AssertionError(errmsg)
    
    # Should have the nested schema
    if "database" not in parent_schema.nested_schemas:
        errmsg = "database should be in nested_schemas"
        raise AssertionError(errmsg)
    
    if parent_schema.nested_schemas["database"] is not child_schema:
        errmsg = "nested schema should be the child_schema"
        raise AssertionError(errmsg)
    
    return


def test_config_schema_get_definition_direct():
    """
        Test that get_definition() returns direct key definitions.
    """
    schema = ConfigSchema()
    schema.define("database.host", str, default="localhost")
    
    definition = schema.get_definition("database.host")
    
    if definition is None:
        errmsg = "get_definition should return the definition"
        raise AssertionError(errmsg)
    
    if definition.key != "database.host":
        errmsg = f"Expected key 'database.host', got {definition.key}"
        raise AssertionError(errmsg)
    
    return


def test_config_schema_get_definition_nested():
    """
        Test that get_definition() returns nested key definitions.
    """
    parent_schema = ConfigSchema()
    child_schema = ConfigSchema()
    child_schema.define("host", str, default="localhost")
    parent_schema.nested("database", child_schema)
    
    definition = parent_schema.get_definition("database.host")
    
    if definition is None:
        errmsg = "get_definition should return the nested definition"
        raise AssertionError(errmsg)
    
    if definition.key != "host":
        errmsg = f"Expected key 'host', got {definition.key}"
        raise AssertionError(errmsg)
    
    return


def test_config_schema_get_definition_not_found():
    """
        Test that get_definition() returns None for unknown keys.
    """
    schema = ConfigSchema()
    schema.define("database.host", str)
    
    definition = schema.get_definition("unknown.key")
    
    if definition is not None:
        errmsg = "get_definition should return None for unknown keys"
        raise AssertionError(errmsg)
    
    return


def test_config_schema_get_all_definitions():
    """
        Test that get_all_definitions() returns all definitions including nested.
    """
    parent_schema = ConfigSchema()
    parent_schema.define("app.name", str)
    
    child_schema = ConfigSchema()
    child_schema.define("host", str)
    child_schema.define("port", int)
    parent_schema.nested("database", child_schema)
    
    all_defs = parent_schema.get_all_definitions()
    
    if len(all_defs) != 3:
        errmsg = f"Expected 3 definitions, got {len(all_defs)}"
        raise AssertionError(errmsg)
    
    if "app.name" not in all_defs:
        errmsg = "app.name should be in all_definitions"
        raise AssertionError(errmsg)
    
    if "database.host" not in all_defs:
        errmsg = "database.host should be in all_definitions"
        raise AssertionError(errmsg)
    
    if "database.port" not in all_defs:
        errmsg = "database.port should be in all_definitions"
        raise AssertionError(errmsg)
    
    return


# =============================================================================
# Unit Tests for coerce_value
# =============================================================================

def test_coerce_value_string_to_int():
    """
        Test that coerce_value converts string to int.
    """
    result = coerce_value("42", int)
    
    if result != 42:
        errmsg = f"Expected 42, got {result}"
        raise AssertionError(errmsg)
    
    if not isinstance(result, int):
        errmsg = f"Expected int type, got {type(result)}"
        raise AssertionError(errmsg)
    
    return


def test_coerce_value_string_to_float():
    """
        Test that coerce_value converts string to float.
    """
    result = coerce_value("3.14", float)
    
    if abs(result - 3.14) > 0.001:
        errmsg = f"Expected 3.14, got {result}"
        raise AssertionError(errmsg)
    
    if not isinstance(result, float):
        errmsg = f"Expected float type, got {type(result)}"
        raise AssertionError(errmsg)
    
    return


def test_coerce_value_string_to_bool_true():
    """
        Test that coerce_value converts string to bool (true values).
    """
    true_values = ["true", "True", "TRUE", "yes", "Yes", "YES", "1", "on", "ON", "t", "T", "y", "Y"]
    
    for value in true_values:
        result = coerce_value(value, bool)
        if result is not True:
            errmsg = f"Expected True for '{value}', got {result}"
            raise AssertionError(errmsg)
    
    return


def test_coerce_value_string_to_bool_false():
    """
        Test that coerce_value converts string to bool (false values).
    """
    false_values = ["false", "False", "FALSE", "no", "No", "NO", "0", "off", "OFF", "f", "F", "n", "N"]
    
    for value in false_values:
        result = coerce_value(value, bool)
        if result is not False:
            errmsg = f"Expected False for '{value}', got {result}"
            raise AssertionError(errmsg)
    
    return


def test_coerce_value_string_to_list():
    """
        Test that coerce_value converts JSON string to list.
    """
    result = coerce_value('[1, 2, 3]', list)
    
    if result != [1, 2, 3]:
        errmsg = f"Expected [1, 2, 3], got {result}"
        raise AssertionError(errmsg)
    
    if not isinstance(result, list):
        errmsg = f"Expected list type, got {type(result)}"
        raise AssertionError(errmsg)
    
    return


def test_coerce_value_string_to_dict():
    """
        Test that coerce_value converts JSON string to dict.
    """
    result = coerce_value('{"key": "value"}', dict)
    
    if result != {"key": "value"}:
        errmsg = f"Expected {{'key': 'value'}}, got {result}"
        raise AssertionError(errmsg)
    
    if not isinstance(result, dict):
        errmsg = f"Expected dict type, got {type(result)}"
        raise AssertionError(errmsg)
    
    return


def test_coerce_value_same_type():
    """
        Test that coerce_value returns value as-is when already correct type.
    """
    # String
    result = coerce_value("hello", str)
    if result != "hello":
        errmsg = f"Expected 'hello', got {result}"
        raise AssertionError(errmsg)
    
    # Int
    result = coerce_value(42, int)
    if result != 42:
        errmsg = f"Expected 42, got {result}"
        raise AssertionError(errmsg)
    
    # Float
    result = coerce_value(3.14, float)
    if abs(result - 3.14) > 0.001:
        errmsg = f"Expected 3.14, got {result}"
        raise AssertionError(errmsg)
    
    # Bool
    result = coerce_value(True, bool)
    if result is not True:
        errmsg = f"Expected True, got {result}"
        raise AssertionError(errmsg)
    
    # List
    result = coerce_value([1, 2], list)
    if result != [1, 2]:
        errmsg = f"Expected [1, 2], got {result}"
        raise AssertionError(errmsg)
    
    # Dict
    result = coerce_value({"a": 1}, dict)
    if result != {"a": 1}:
        errmsg = f"Expected {{'a': 1}}, got {result}"
        raise AssertionError(errmsg)
    
    return


def test_coerce_value_int_to_float():
    """
        Test that coerce_value converts int to float.
    """
    result = coerce_value(42, float)
    
    if abs(result - 42.0) > 0.001:
        errmsg = f"Expected 42.0, got {result}"
        raise AssertionError(errmsg)
    
    if not isinstance(result, float):
        errmsg = f"Expected float type, got {type(result)}"
        raise AssertionError(errmsg)
    
    return


def test_coerce_value_float_to_int():
    """
        Test that coerce_value converts float to int.
    """
    result = coerce_value(42.9, int)
    
    if result != 42:
        errmsg = f"Expected 42, got {result}"
        raise AssertionError(errmsg)
    
    if not isinstance(result, int):
        errmsg = f"Expected int type, got {type(result)}"
        raise AssertionError(errmsg)
    
    return


def test_coerce_value_invalid_string_to_int():
    """
        Test that coerce_value raises ValueError for invalid string to int.
    """
    try:
        coerce_value("not_a_number", int)
        errmsg = "Expected ValueError for invalid string to int"
        raise AssertionError(errmsg)
    except ValueError:
        pass  # Expected
    
    return


def test_coerce_value_invalid_string_to_bool():
    """
        Test that coerce_value raises ValueError for invalid string to bool.
    """
    try:
        coerce_value("maybe", bool)
        errmsg = "Expected ValueError for invalid string to bool"
        raise AssertionError(errmsg)
    except ValueError:
        pass  # Expected
    
    return


def test_coerce_value_invalid_string_to_list():
    """
        Test that coerce_value raises ValueError for invalid JSON string to list.
    """
    try:
        coerce_value("not json", list)
        errmsg = "Expected ValueError for invalid JSON string to list"
        raise AssertionError(errmsg)
    except ValueError:
        pass  # Expected
    
    return


def test_coerce_value_invalid_string_to_dict():
    """
        Test that coerce_value raises ValueError for invalid JSON string to dict.
    """
    try:
        coerce_value("not json", dict)
        errmsg = "Expected ValueError for invalid JSON string to dict"
        raise AssertionError(errmsg)
    except ValueError:
        pass  # Expected
    
    return


# =============================================================================
# Property-Based Tests for Type Coercion
# =============================================================================

# Feature: configuration-system, Property 10: Type Coercion
# *For any* string configuration value and declared type in the schema, the value
# SHALL be coerced to the declared type (e.g., "true" to True, "42" to 42) when possible.
# **Validates: Requirements 3.8**

def test_property_10_type_coercion():
    """
        Property 10: Type Coercion
        
        For any string configuration value and declared type in the schema,
        the value SHALL be coerced to the declared type when possible.
        
        **Feature: configuration-system, Property 10: Type Coercion**
        **Validates: Requirements 3.8**
    """
    # Run 100 iterations with random data
    for iteration in range(100):
        # Test string to int coercion
        int_value = generate_random_int()
        str_int = str(int_value)
        coerced_int = coerce_value(str_int, int)
        if coerced_int != int_value:
            errmsg = f"Iteration {iteration}: String '{str_int}' should coerce to int {int_value}, got {coerced_int}"
            raise AssertionError(errmsg)
        
        # Test string to float coercion
        float_value = generate_random_float()
        str_float = str(float_value)
        coerced_float = coerce_value(str_float, float)
        if abs(coerced_float - float_value) > 0.0001:
            errmsg = f"Iteration {iteration}: String '{str_float}' should coerce to float {float_value}, got {coerced_float}"
            raise AssertionError(errmsg)
        
        # Test string to bool coercion (true values)
        true_strings = ["true", "True", "TRUE", "yes", "Yes", "1", "on", "t", "y"]
        true_str = random.choice(true_strings)
        coerced_bool = coerce_value(true_str, bool)
        if coerced_bool is not True:
            errmsg = f"Iteration {iteration}: String '{true_str}' should coerce to True, got {coerced_bool}"
            raise AssertionError(errmsg)
        
        # Test string to bool coercion (false values)
        false_strings = ["false", "False", "FALSE", "no", "No", "0", "off", "f", "n"]
        false_str = random.choice(false_strings)
        coerced_bool = coerce_value(false_str, bool)
        if coerced_bool is not False:
            errmsg = f"Iteration {iteration}: String '{false_str}' should coerce to False, got {coerced_bool}"
            raise AssertionError(errmsg)
        
        # Test string to list coercion (JSON)
        list_value = generate_random_list()
        str_list = json.dumps(list_value)
        coerced_list = coerce_value(str_list, list)
        if coerced_list != list_value:
            errmsg = f"Iteration {iteration}: String '{str_list}' should coerce to list {list_value}, got {coerced_list}"
            raise AssertionError(errmsg)
        
        # Test string to dict coercion (JSON)
        dict_value = generate_random_dict()
        str_dict = json.dumps(dict_value)
        coerced_dict = coerce_value(str_dict, dict)
        if coerced_dict != dict_value:
            errmsg = f"Iteration {iteration}: String '{str_dict}' should coerce to dict {dict_value}, got {coerced_dict}"
            raise AssertionError(errmsg)
    
    return


def test_property_10_type_coercion_identity():
    """
        Property 10 (Extended): Type Coercion Identity
        
        For any value that is already the target type, coercion SHALL return
        the same value unchanged.
        
        **Feature: configuration-system, Property 10: Type Coercion**
        **Validates: Requirements 3.8**
    """
    # Run 100 iterations with random data
    for iteration in range(100):
        # Test int identity
        int_value = generate_random_int()
        coerced = coerce_value(int_value, int)
        if coerced != int_value:
            errmsg = f"Iteration {iteration}: Int {int_value} should remain unchanged, got {coerced}"
            raise AssertionError(errmsg)
        
        # Test float identity
        float_value = generate_random_float()
        coerced = coerce_value(float_value, float)
        if abs(coerced - float_value) > 0.0001:
            errmsg = f"Iteration {iteration}: Float {float_value} should remain unchanged, got {coerced}"
            raise AssertionError(errmsg)
        
        # Test bool identity
        bool_value = generate_random_bool()
        coerced = coerce_value(bool_value, bool)
        if coerced != bool_value:
            errmsg = f"Iteration {iteration}: Bool {bool_value} should remain unchanged, got {coerced}"
            raise AssertionError(errmsg)
        
        # Test string identity
        str_value = generate_random_string()
        coerced = coerce_value(str_value, str)
        if coerced != str_value:
            errmsg = f"Iteration {iteration}: String '{str_value}' should remain unchanged, got '{coerced}'"
            raise AssertionError(errmsg)
        
        # Test list identity
        list_value = generate_random_list()
        coerced = coerce_value(list_value, list)
        if coerced != list_value:
            errmsg = f"Iteration {iteration}: List {list_value} should remain unchanged, got {coerced}"
            raise AssertionError(errmsg)
        
        # Test dict identity
        dict_value = generate_random_dict()
        coerced = coerce_value(dict_value, dict)
        if coerced != dict_value:
            errmsg = f"Iteration {iteration}: Dict {dict_value} should remain unchanged, got {coerced}"
            raise AssertionError(errmsg)
    
    return


# =============================================================================
# Unit Tests for Schema Validation
# =============================================================================

def test_schema_validate_empty_values():
    """
        Test that validate() returns no errors for empty values with no required keys.
    """
    schema = ConfigSchema()
    schema.define("optional.key", str)
    
    errors = schema.validate({})
    
    if len(errors) != 0:
        errmsg = f"Expected no errors, got {len(errors)}"
        raise AssertionError(errmsg)
    
    return


def test_schema_validate_required_key_missing():
    """
        Test that validate() returns error for missing required key.
    """
    schema = ConfigSchema()
    schema.define("required.key", str, required=True)
    
    errors = schema.validate({})
    
    if len(errors) != 1:
        errmsg = f"Expected 1 error, got {len(errors)}"
        raise AssertionError(errmsg)
    
    if errors[0].key != "required.key":
        errmsg = f"Expected key 'required.key', got {errors[0].key}"
        raise AssertionError(errmsg)
    
    if errors[0].constraint != "required":
        errmsg = f"Expected constraint 'required', got {errors[0].constraint}"
        raise AssertionError(errmsg)
    
    return


def test_schema_validate_required_key_present():
    """
        Test that validate() returns no errors when required key is present.
    """
    schema = ConfigSchema()
    schema.define("required.key", str, required=True)
    
    errors = schema.validate({"required": {"key": "value"}})
    
    if len(errors) != 0:
        errmsg = f"Expected no errors, got {len(errors)}: {[e.message for e in errors]}"
        raise AssertionError(errmsg)
    
    return


def test_schema_validate_type_error():
    """
        Test that validate() returns error for invalid type.
    """
    schema = ConfigSchema()
    schema.define("int.key", int)
    
    errors = schema.validate({"int": {"key": "not_a_number"}})
    
    if len(errors) != 1:
        errmsg = f"Expected 1 error, got {len(errors)}"
        raise AssertionError(errmsg)
    
    if errors[0].constraint != "type":
        errmsg = f"Expected constraint 'type', got {errors[0].constraint}"
        raise AssertionError(errmsg)
    
    return


def test_schema_validate_type_coercion_success():
    """
        Test that validate() succeeds when type can be coerced.
    """
    schema = ConfigSchema()
    schema.define("int.key", int)
    
    # String "42" can be coerced to int
    errors = schema.validate({"int": {"key": "42"}})
    
    if len(errors) != 0:
        errmsg = f"Expected no errors, got {len(errors)}: {[e.message for e in errors]}"
        raise AssertionError(errmsg)
    
    return


def test_schema_validate_choices_valid():
    """
        Test that validate() succeeds when value is in choices.
    """
    schema = ConfigSchema()
    schema.define("log.level", str, choices=["DEBUG", "INFO", "WARNING", "ERROR"])
    
    errors = schema.validate({"log": {"level": "INFO"}})
    
    if len(errors) != 0:
        errmsg = f"Expected no errors, got {len(errors)}: {[e.message for e in errors]}"
        raise AssertionError(errmsg)
    
    return


def test_schema_validate_choices_invalid():
    """
        Test that validate() returns error when value is not in choices.
    """
    schema = ConfigSchema()
    schema.define("log.level", str, choices=["DEBUG", "INFO", "WARNING", "ERROR"])
    
    errors = schema.validate({"log": {"level": "INVALID"}})
    
    if len(errors) != 1:
        errmsg = f"Expected 1 error, got {len(errors)}"
        raise AssertionError(errmsg)
    
    if errors[0].constraint != "choices":
        errmsg = f"Expected constraint 'choices', got {errors[0].constraint}"
        raise AssertionError(errmsg)
    
    return


def test_schema_validate_custom_validator_pass():
    """
        Test that validate() succeeds when custom validator passes.
    """
    def port_validator(value: int) -> bool:
        return 1 <= value <= 65535
    
    schema = ConfigSchema()
    schema.define("server.port", int, validator=port_validator)
    
    errors = schema.validate({"server": {"port": 8080}})
    
    if len(errors) != 0:
        errmsg = f"Expected no errors, got {len(errors)}: {[e.message for e in errors]}"
        raise AssertionError(errmsg)
    
    return


def test_schema_validate_custom_validator_fail():
    """
        Test that validate() returns error when custom validator fails.
    """
    def port_validator(value: int) -> bool:
        return 1 <= value <= 65535
    
    schema = ConfigSchema()
    schema.define("server.port", int, validator=port_validator)
    
    errors = schema.validate({"server": {"port": 70000}})
    
    if len(errors) != 1:
        errmsg = f"Expected 1 error, got {len(errors)}"
        raise AssertionError(errmsg)
    
    if errors[0].constraint != "custom":
        errmsg = f"Expected constraint 'custom', got {errors[0].constraint}"
        raise AssertionError(errmsg)
    
    return


def test_schema_validate_custom_validator_exception():
    """
        Test that validate() handles custom validator exceptions.
    """
    def bad_validator(value: Any) -> bool:
        raise RuntimeError("Validator error")
    
    schema = ConfigSchema()
    schema.define("test.key", str, validator=bad_validator)
    
    errors = schema.validate({"test": {"key": "value"}})
    
    if len(errors) != 1:
        errmsg = f"Expected 1 error, got {len(errors)}"
        raise AssertionError(errmsg)
    
    if errors[0].constraint != "custom":
        errmsg = f"Expected constraint 'custom', got {errors[0].constraint}"
        raise AssertionError(errmsg)
    
    if "exception" not in errors[0].message.lower():
        errmsg = f"Expected 'exception' in message, got {errors[0].message}"
        raise AssertionError(errmsg)
    
    return


def test_schema_validate_multiple_errors():
    """
        Test that validate() returns all errors, not just the first one.
    """
    schema = ConfigSchema()
    schema.define("required1", str, required=True)
    schema.define("required2", str, required=True)
    schema.define("required3", str, required=True)
    
    errors = schema.validate({})
    
    if len(errors) != 3:
        errmsg = f"Expected 3 errors, got {len(errors)}"
        raise AssertionError(errmsg)
    
    return


# =============================================================================
# Property-Based Tests for Schema Validation
# =============================================================================

# Feature: configuration-system, Property 9: Schema Validation Completeness
# *For any* configuration and schema, validation SHALL check all values against
# their schema definitions, and if any validation fails, ConfigurationValidationError
# SHALL be raised with details about all failures.
# **Validates: Requirements 3.1, 3.2, 3.6, 3.7**

def test_property_9_schema_validation_completeness():
    """
        Property 9: Schema Validation Completeness
        
        For any configuration and schema, validation SHALL check all values
        against their schema definitions, and if any validation fails,
        all failures SHALL be reported.
        
        **Feature: configuration-system, Property 9: Schema Validation Completeness**
        **Validates: Requirements 3.1, 3.2, 3.6, 3.7**
    """
    # Run 100 iterations with random data
    for iteration in range(100):
        # Generate a random schema with multiple keys
        schema = ConfigSchema()
        num_keys = random.randint(1, 5)
        required_keys = []
        optional_keys = []
        
        for i in range(num_keys):
            key = f"key{i}"
            key_type = random.choice([str, int, bool])
            is_required = random.choice([True, False])
            
            schema.define(key, key_type, required=is_required)
            
            if is_required:
                required_keys.append((key, key_type))
            else:
                optional_keys.append((key, key_type))
        
        # Generate values - randomly include or exclude keys
        values = {}
        missing_required = []
        
        for key, key_type in required_keys:
            if random.choice([True, False]):
                # Include the key with valid value
                if key_type is str:
                    values[key] = generate_random_string()
                elif key_type is int:
                    values[key] = generate_random_int()
                else:
                    values[key] = generate_random_bool()
            else:
                # Missing required key
                missing_required.append(key)
        
        for key, key_type in optional_keys:
            if random.choice([True, False]):
                # Include the key with valid value
                if key_type is str:
                    values[key] = generate_random_string()
                elif key_type is int:
                    values[key] = generate_random_int()
                else:
                    values[key] = generate_random_bool()
        
        # Validate
        errors = schema.validate(values)
        
        # Property: All missing required keys SHALL be reported
        error_keys = [e.key for e in errors]
        for missing_key in missing_required:
            if missing_key not in error_keys:
                errmsg = f"Iteration {iteration}: Missing required key '{missing_key}' should be in errors"
                raise AssertionError(errmsg)
        
        # Property: Number of errors SHALL equal number of missing required keys
        if len(errors) != len(missing_required):
            errmsg = f"Iteration {iteration}: Expected {len(missing_required)} errors, got {len(errors)}"
            raise AssertionError(errmsg)
    
    return


def test_property_9_schema_validation_type_checking():
    """
        Property 9 (Extended): Schema Validation Type Checking
        
        For any configuration value with an invalid type that cannot be coerced,
        validation SHALL report a type error.
        
        **Feature: configuration-system, Property 9: Schema Validation Completeness**
        **Validates: Requirements 3.1, 3.2, 3.6, 3.7**
    """
    # Run 100 iterations with random data
    for iteration in range(100):
        # Create schema with int key
        schema = ConfigSchema()
        key = generate_random_key()
        schema.define(key, int)
        
        # Generate an invalid value (string that can't be coerced to int)
        invalid_value = generate_random_string(5, 20)
        # Make sure it's not a valid number
        while invalid_value.lstrip('-').isdigit():
            invalid_value = generate_random_string(5, 20)
        
        # Build nested values dict
        parts = key.split(".")
        values = {}
        current = values
        for i, part in enumerate(parts[:-1]):
            current[part] = {}
            current = current[part]
        current[parts[-1]] = invalid_value
        
        # Validate
        errors = schema.validate(values)
        
        # Property: Type error SHALL be reported
        if len(errors) != 1:
            errmsg = f"Iteration {iteration}: Expected 1 type error, got {len(errors)}"
            raise AssertionError(errmsg)
        
        if errors[0].constraint != "type":
            errmsg = f"Iteration {iteration}: Expected 'type' constraint, got {errors[0].constraint}"
            raise AssertionError(errmsg)
    
    return


# Feature: configuration-system, Property 12: Enum Constraint Validation
# *For any* configuration key with an enum constraint (choices), values outside
# the allowed choices SHALL fail validation.
# **Validates: Requirements 3.10**

def test_property_12_enum_constraint_validation():
    """
        Property 12: Enum Constraint Validation
        
        For any configuration key with an enum constraint (choices), values
        outside the allowed choices SHALL fail validation.
        
        **Feature: configuration-system, Property 12: Enum Constraint Validation**
        **Validates: Requirements 3.10**
    """
    # Run 100 iterations with random data
    for iteration in range(100):
        # Generate random choices
        num_choices = random.randint(2, 6)
        choices = [generate_random_string(3, 10) for _ in range(num_choices)]
        # Ensure choices are unique
        choices = list(set(choices))
        if len(choices) < 2:
            choices = ["option1", "option2", "option3"]
        
        # Create schema with choices constraint
        schema = ConfigSchema()
        key = generate_random_key()
        schema.define(key, str, choices=choices)
        
        # Test with valid choice
        valid_choice = random.choice(choices)
        parts = key.split(".")
        values = {}
        current = values
        for i, part in enumerate(parts[:-1]):
            current[part] = {}
            current = current[part]
        current[parts[-1]] = valid_choice
        
        errors = schema.validate(values)
        
        # Property: Valid choice SHALL pass validation
        if len(errors) != 0:
            errmsg = f"Iteration {iteration}: Valid choice '{valid_choice}' should pass validation, got errors: {[e.message for e in errors]}"
            raise AssertionError(errmsg)
        
        # Test with invalid choice
        invalid_choice = generate_random_string(10, 20)
        while invalid_choice in choices:
            invalid_choice = generate_random_string(10, 20)
        
        current[parts[-1]] = invalid_choice
        
        errors = schema.validate(values)
        
        # Property: Invalid choice SHALL fail validation
        if len(errors) != 1:
            errmsg = f"Iteration {iteration}: Invalid choice '{invalid_choice}' should fail validation, got {len(errors)} errors"
            raise AssertionError(errmsg)
        
        if errors[0].constraint != "choices":
            errmsg = f"Iteration {iteration}: Expected 'choices' constraint, got {errors[0].constraint}"
            raise AssertionError(errmsg)
    
    return


def test_property_12_enum_constraint_all_choices_valid():
    """
        Property 12 (Extended): All Enum Choices Valid
        
        For any configuration key with an enum constraint, ALL values in the
        choices list SHALL pass validation.
        
        **Feature: configuration-system, Property 12: Enum Constraint Validation**
        **Validates: Requirements 3.10**
    """
    # Run 100 iterations with random data
    for iteration in range(100):
        # Generate random choices
        num_choices = random.randint(2, 8)
        choices = [generate_random_string(3, 15) for _ in range(num_choices)]
        # Ensure choices are unique
        choices = list(set(choices))
        if len(choices) < 2:
            choices = ["opt1", "opt2", "opt3", "opt4"]
        
        # Create schema with choices constraint
        schema = ConfigSchema()
        key = "test.key"
        schema.define(key, str, choices=choices)
        
        # Test each choice
        for choice in choices:
            values = {"test": {"key": choice}}
            errors = schema.validate(values)
            
            # Property: Every choice in the list SHALL pass validation
            if len(errors) != 0:
                errmsg = f"Iteration {iteration}: Choice '{choice}' from choices list should pass validation"
                raise AssertionError(errmsg)
    
    return


# =============================================================================
# Unit Tests for Nested Schema Validation
# =============================================================================

def test_nested_schema_validation_basic():
    """
        Test that nested schema validation works for basic cases.
    """
    # Create nested schema
    db_schema = ConfigSchema()
    db_schema.define("host", str, required=True)
    db_schema.define("port", int, required=True)
    
    # Create parent schema
    parent_schema = ConfigSchema()
    parent_schema.nested("database", db_schema)
    
    # Valid values
    values = {
        "database": {
            "host": "localhost",
            "port": 5432
        }
    }
    
    errors = parent_schema.validate(values)
    
    if len(errors) != 0:
        errmsg = f"Expected no errors, got {len(errors)}: {[e.message for e in errors]}"
        raise AssertionError(errmsg)
    
    return


def test_nested_schema_validation_missing_required():
    """
        Test that nested schema validation reports missing required keys.
    """
    # Create nested schema
    db_schema = ConfigSchema()
    db_schema.define("host", str, required=True)
    db_schema.define("port", int, required=True)
    
    # Create parent schema
    parent_schema = ConfigSchema()
    parent_schema.nested("database", db_schema)
    
    # Missing port
    values = {
        "database": {
            "host": "localhost"
        }
    }
    
    errors = parent_schema.validate(values)
    
    if len(errors) != 1:
        errmsg = f"Expected 1 error, got {len(errors)}"
        raise AssertionError(errmsg)
    
    if errors[0].key != "database.port":
        errmsg = f"Expected key 'database.port', got {errors[0].key}"
        raise AssertionError(errmsg)
    
    return


def test_nested_schema_validation_type_error():
    """
        Test that nested schema validation reports type errors.
    """
    # Create nested schema
    db_schema = ConfigSchema()
    db_schema.define("port", int)
    
    # Create parent schema
    parent_schema = ConfigSchema()
    parent_schema.nested("database", db_schema)
    
    # Invalid type
    values = {
        "database": {
            "port": "not_a_number"
        }
    }
    
    errors = parent_schema.validate(values)
    
    if len(errors) != 1:
        errmsg = f"Expected 1 error, got {len(errors)}"
        raise AssertionError(errmsg)
    
    if errors[0].constraint != "type":
        errmsg = f"Expected constraint 'type', got {errors[0].constraint}"
        raise AssertionError(errmsg)
    
    return


def test_nested_schema_validation_deeply_nested():
    """
        Test that deeply nested schema validation works.
    """
    # Create deeply nested schemas
    credentials_schema = ConfigSchema()
    credentials_schema.define("username", str, required=True)
    credentials_schema.define("password", str, required=True, sensitive=True)
    
    db_schema = ConfigSchema()
    db_schema.define("host", str, required=True)
    db_schema.nested("credentials", credentials_schema)
    
    parent_schema = ConfigSchema()
    parent_schema.nested("database", db_schema)
    
    # Valid values
    values = {
        "database": {
            "host": "localhost",
            "credentials": {
                "username": "admin",
                "password": "secret"
            }
        }
    }
    
    errors = parent_schema.validate(values)
    
    if len(errors) != 0:
        errmsg = f"Expected no errors, got {len(errors)}: {[e.message for e in errors]}"
        raise AssertionError(errmsg)
    
    return


def test_nested_schema_validation_missing_nested_section():
    """
        Test that validation handles missing nested sections gracefully.
    """
    # Create nested schema with required key
    db_schema = ConfigSchema()
    db_schema.define("host", str, required=True)
    
    # Create parent schema
    parent_schema = ConfigSchema()
    parent_schema.nested("database", db_schema)
    
    # Missing entire database section
    values = {}
    
    errors = parent_schema.validate(values)
    
    # The nested schema's required key should be reported as missing
    # via the get_all_definitions path
    if len(errors) != 1:
        errmsg = f"Expected 1 error for missing required nested key, got {len(errors)}"
        raise AssertionError(errmsg)
    
    return


# =============================================================================
# Property-Based Tests for Nested Schema Validation
# =============================================================================

# Feature: configuration-system, Property 11: Nested Schema Validation
# *For any* nested configuration structure with a nested schema definition,
# validation SHALL recursively validate all nested values against their
# respective schema definitions.
# **Validates: Requirements 3.9**

def test_property_11_nested_schema_validation():
    """
        Property 11: Nested Schema Validation
        
        For any nested configuration structure with a nested schema definition,
        validation SHALL recursively validate all nested values against their
        respective schema definitions.
        
        **Feature: configuration-system, Property 11: Nested Schema Validation**
        **Validates: Requirements 3.9**
    """
    # Run 100 iterations with random data
    for iteration in range(100):
        # Create a nested schema structure
        child_schema = ConfigSchema()
        num_child_keys = random.randint(1, 3)
        child_required_keys = []
        
        for i in range(num_child_keys):
            key = f"child_key{i}"
            key_type = random.choice([str, int, bool])
            is_required = random.choice([True, False])
            child_schema.define(key, key_type, required=is_required)
            if is_required:
                child_required_keys.append((key, key_type))
        
        # Create parent schema with nested child
        parent_schema = ConfigSchema()
        parent_prefix = "nested"
        parent_schema.nested(parent_prefix, child_schema)
        
        # Generate valid values for all required keys
        child_values = {}
        for key, key_type in child_required_keys:
            if key_type is str:
                child_values[key] = generate_random_string()
            elif key_type is int:
                child_values[key] = generate_random_int()
            else:
                child_values[key] = generate_random_bool()
        
        values = {parent_prefix: child_values}
        
        # Validate - should pass with all required keys present
        errors = parent_schema.validate(values)
        
        # Property: Valid nested values SHALL pass validation
        if len(errors) != 0:
            errmsg = f"Iteration {iteration}: Valid nested values should pass validation, got errors: {[e.message for e in errors]}"
            raise AssertionError(errmsg)
        
        # Now remove a required key if any exist
        if len(child_required_keys) > 0:
            removed_key, _ = random.choice(child_required_keys)
            del child_values[removed_key]
            
            errors = parent_schema.validate(values)
            
            # Property: Missing required nested key SHALL be reported
            if len(errors) != 1:
                errmsg = f"Iteration {iteration}: Expected 1 error for missing nested key, got {len(errors)}"
                raise AssertionError(errmsg)
            
            expected_full_key = f"{parent_prefix}.{removed_key}"
            if errors[0].key != expected_full_key:
                errmsg = f"Iteration {iteration}: Expected key '{expected_full_key}', got '{errors[0].key}'"
                raise AssertionError(errmsg)
    
    return


def test_property_11_nested_schema_type_validation():
    """
        Property 11 (Extended): Nested Schema Type Validation
        
        For any nested configuration value with an invalid type, validation
        SHALL report the error with the full nested key path.
        
        **Feature: configuration-system, Property 11: Nested Schema Validation**
        **Validates: Requirements 3.9**
    """
    # Run 100 iterations with random data
    for iteration in range(100):
        # Create a nested schema with int key
        child_schema = ConfigSchema()
        child_key = "port"
        child_schema.define(child_key, int)
        
        # Create parent schema
        parent_schema = ConfigSchema()
        parent_prefix = "server"
        parent_schema.nested(parent_prefix, child_schema)
        
        # Generate invalid value (string that can't be coerced to int)
        invalid_value = generate_random_string(5, 15)
        while invalid_value.lstrip('-').isdigit():
            invalid_value = generate_random_string(5, 15)
        
        values = {parent_prefix: {child_key: invalid_value}}
        
        # Validate
        errors = parent_schema.validate(values)
        
        # Property: Type error SHALL be reported with full nested key path
        if len(errors) != 1:
            errmsg = f"Iteration {iteration}: Expected 1 type error, got {len(errors)}"
            raise AssertionError(errmsg)
        
        expected_full_key = f"{parent_prefix}.{child_key}"
        if errors[0].key != expected_full_key:
            errmsg = f"Iteration {iteration}: Expected key '{expected_full_key}', got '{errors[0].key}'"
            raise AssertionError(errmsg)
        
        if errors[0].constraint != "type":
            errmsg = f"Iteration {iteration}: Expected 'type' constraint, got {errors[0].constraint}"
            raise AssertionError(errmsg)
    
    return


def test_property_11_deeply_nested_schema_validation():
    """
        Property 11 (Extended): Deeply Nested Schema Validation
        
        For any deeply nested configuration structure (3+ levels), validation
        SHALL correctly validate all levels and report errors with full paths.
        
        **Feature: configuration-system, Property 11: Nested Schema Validation**
        **Validates: Requirements 3.9**
    """
    # Run 100 iterations with random data
    for iteration in range(100):
        # Create 3-level nested schema
        level3_schema = ConfigSchema()
        level3_key = "value"
        level3_schema.define(level3_key, str, required=True)
        
        level2_schema = ConfigSchema()
        level2_prefix = "level2"
        level2_schema.nested(level2_prefix, level3_schema)
        
        level1_schema = ConfigSchema()
        level1_prefix = "level1"
        level1_schema.nested(level1_prefix, level2_schema)
        
        # Valid values
        valid_value = generate_random_string()
        values = {
            level1_prefix: {
                level2_prefix: {
                    level3_key: valid_value
                }
            }
        }
        
        errors = level1_schema.validate(values)
        
        # Property: Valid deeply nested values SHALL pass validation
        if len(errors) != 0:
            errmsg = f"Iteration {iteration}: Valid deeply nested values should pass, got errors: {[e.message for e in errors]}"
            raise AssertionError(errmsg)
        
        # Remove the deeply nested required key
        del values[level1_prefix][level2_prefix][level3_key]
        
        errors = level1_schema.validate(values)
        
        # Property: Missing deeply nested required key SHALL be reported with full path
        if len(errors) != 1:
            errmsg = f"Iteration {iteration}: Expected 1 error for missing deeply nested key, got {len(errors)}"
            raise AssertionError(errmsg)
        
        expected_full_key = f"{level1_prefix}.{level2_prefix}.{level3_key}"
        if errors[0].key != expected_full_key:
            errmsg = f"Iteration {iteration}: Expected key '{expected_full_key}', got '{errors[0].key}'"
            raise AssertionError(errmsg)
    
    return
