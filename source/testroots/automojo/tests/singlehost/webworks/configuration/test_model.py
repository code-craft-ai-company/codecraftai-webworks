"""
    Tests for the configuration model module.
    
    This module contains unit tests and property tests for the ConfigurationModel
    and ConfigNamespace classes.
"""

import random
import string
from typing import Any, Dict, List

from automojo.webworks.configuration import (
    ConfigurationModel,
    ConfigNamespace,
    ConfigRegistry,
    ConfigSchema,
    ConfigSourceType,
    ConfigValue,
    ConfigValueMetadata,
    ConfigurationError,
    ConfigurationTypeError
)


# =============================================================================
# Helper Functions for Test Data Generation
# =============================================================================

def generate_random_string(min_length: int = 1, max_length: int = 20) -> str:
    """
        Generate a random string for testing.
        
        :param min_length: Minimum string length.
        :param max_length: Maximum string length.
        
        :returns: A random string.
    """
    length = random.randint(min_length, max_length)
    # Start with a letter to ensure valid Python identifier
    first_char = random.choice(string.ascii_letters)
    if length == 1:
        return first_char
    remaining_chars = string.ascii_letters + string.digits + "_"
    return first_char + "".join(random.choice(remaining_chars) for _ in range(length - 1))


def generate_random_key() -> str:
    """
        Generate a random configuration key in dot-notation.
        
        :returns: A random key like "section.subsection.key".
    """
    depth = random.randint(1, 3)
    parts = [generate_random_string(3, 10) for _ in range(depth)]
    return ".".join(parts)


def generate_random_int() -> int:
    """
        Generate a random integer for testing.
        
        :returns: A random integer.
    """
    return random.randint(-10000, 10000)


def generate_random_float() -> float:
    """
        Generate a random float for testing.
        
        :returns: A random float.
    """
    return random.uniform(-10000.0, 10000.0)


def generate_random_bool() -> bool:
    """
        Generate a random boolean for testing.
        
        :returns: A random boolean.
    """
    return random.choice([True, False])


def generate_random_list() -> List[Any]:
    """
        Generate a random list for testing.
        
        :returns: A random list.
    """
    length = random.randint(0, 5)
    return [random.randint(0, 100) for _ in range(length)]


def generate_random_dict() -> Dict[str, Any]:
    """
        Generate a random dictionary for testing.
        
        :returns: A random dictionary.
    """
    length = random.randint(0, 3)
    return {generate_random_string(3, 8): random.randint(0, 100) for _ in range(length)}


# =============================================================================
# Unit Tests for ConfigurationModel Creation
# =============================================================================

def test_configuration_model_creation():
    """
        Test that ConfigurationModel can be created with a registry.
    """
    registry = ConfigRegistry()
    model = ConfigurationModel(registry)
    
    if model.registry is not registry:
        errmsg = "Expected model.registry to be the provided registry"
        raise AssertionError(errmsg)
    
    return


def test_configuration_model_repr():
    """
        Test that ConfigurationModel has a useful repr.
    """
    schema = ConfigSchema()
    schema.define("test.key", str, default="value")
    
    registry = ConfigRegistry(schema=schema)
    registry.load()
    
    model = ConfigurationModel(registry)
    repr_str = repr(model)
    
    if "ConfigurationModel" not in repr_str:
        errmsg = f"Expected 'ConfigurationModel' in repr, got {repr_str}"
        raise AssertionError(errmsg)
    
    return


# =============================================================================
# Unit Tests for Typed Access Methods
# =============================================================================

def test_get_returns_value():
    """
        Test that get() returns the configuration value.
    """
    schema = ConfigSchema()
    schema.define("database.host", str, default="localhost")
    
    registry = ConfigRegistry(schema=schema)
    registry.load()
    
    model = ConfigurationModel(registry)
    value = model.get("database.host")
    
    if value != "localhost":
        errmsg = f"Expected 'localhost', got {value}"
        raise AssertionError(errmsg)
    
    return


def test_get_with_default():
    """
        Test that get() returns the provided default when key not found.
    """
    registry = ConfigRegistry()
    registry.load()
    
    model = ConfigurationModel(registry)
    value = model.get("nonexistent.key", "default_value")
    
    if value != "default_value":
        errmsg = f"Expected 'default_value', got {value}"
        raise AssertionError(errmsg)
    
    return


def test_get_raises_error_when_key_not_found():
    """
        Test that get() raises ConfigurationError when key not found and no default.
    """
    registry = ConfigRegistry()
    registry.load()
    
    model = ConfigurationModel(registry)
    
    try:
        model.get("nonexistent.key")
        errmsg = "Expected ConfigurationError to be raised"
        raise AssertionError(errmsg)
    except ConfigurationError as e:
        if "nonexistent.key" not in str(e):
            errmsg = f"Expected key name in error message, got {str(e)}"
            raise AssertionError(errmsg)
    
    return


def test_get_str_returns_string():
    """
        Test that get_str() returns a string value.
    """
    schema = ConfigSchema()
    schema.define("test.key", str, default="test_value")
    
    registry = ConfigRegistry(schema=schema)
    registry.load()
    
    model = ConfigurationModel(registry)
    value = model.get_str("test.key")
    
    if not isinstance(value, str):
        errmsg = f"Expected str, got {type(value).__name__}"
        raise AssertionError(errmsg)
    
    if value != "test_value":
        errmsg = f"Expected 'test_value', got {value}"
        raise AssertionError(errmsg)
    
    return


def test_get_str_coerces_int_to_string():
    """
        Test that get_str() coerces an integer to string.
    """
    schema = ConfigSchema()
    schema.define("test.key", int, default=42)
    
    registry = ConfigRegistry(schema=schema)
    registry.load()
    
    model = ConfigurationModel(registry)
    value = model.get_str("test.key")
    
    if not isinstance(value, str):
        errmsg = f"Expected str, got {type(value).__name__}"
        raise AssertionError(errmsg)
    
    if value != "42":
        errmsg = f"Expected '42', got {value}"
        raise AssertionError(errmsg)
    
    return


def test_get_int_returns_integer():
    """
        Test that get_int() returns an integer value.
    """
    schema = ConfigSchema()
    schema.define("test.key", int, default=42)
    
    registry = ConfigRegistry(schema=schema)
    registry.load()
    
    model = ConfigurationModel(registry)
    value = model.get_int("test.key")
    
    if not isinstance(value, int):
        errmsg = f"Expected int, got {type(value).__name__}"
        raise AssertionError(errmsg)
    
    if value != 42:
        errmsg = f"Expected 42, got {value}"
        raise AssertionError(errmsg)
    
    return


def test_get_int_coerces_string_to_int():
    """
        Test that get_int() coerces a string to integer.
    """
    schema = ConfigSchema()
    schema.define("test.key", str, default="123")
    
    registry = ConfigRegistry(schema=schema)
    registry.load()
    
    model = ConfigurationModel(registry)
    value = model.get_int("test.key")
    
    if not isinstance(value, int):
        errmsg = f"Expected int, got {type(value).__name__}"
        raise AssertionError(errmsg)
    
    if value != 123:
        errmsg = f"Expected 123, got {value}"
        raise AssertionError(errmsg)
    
    return


def test_get_float_returns_float():
    """
        Test that get_float() returns a float value.
    """
    schema = ConfigSchema()
    schema.define("test.key", float, default=3.14)
    
    registry = ConfigRegistry(schema=schema)
    registry.load()
    
    model = ConfigurationModel(registry)
    value = model.get_float("test.key")
    
    if not isinstance(value, float):
        errmsg = f"Expected float, got {type(value).__name__}"
        raise AssertionError(errmsg)
    
    if abs(value - 3.14) > 0.001:
        errmsg = f"Expected 3.14, got {value}"
        raise AssertionError(errmsg)
    
    return


def test_get_float_coerces_string_to_float():
    """
        Test that get_float() coerces a string to float.
    """
    schema = ConfigSchema()
    schema.define("test.key", str, default="2.718")
    
    registry = ConfigRegistry(schema=schema)
    registry.load()
    
    model = ConfigurationModel(registry)
    value = model.get_float("test.key")
    
    if not isinstance(value, float):
        errmsg = f"Expected float, got {type(value).__name__}"
        raise AssertionError(errmsg)
    
    if abs(value - 2.718) > 0.001:
        errmsg = f"Expected 2.718, got {value}"
        raise AssertionError(errmsg)
    
    return


def test_get_bool_returns_boolean():
    """
        Test that get_bool() returns a boolean value.
    """
    schema = ConfigSchema()
    schema.define("test.key", bool, default=True)
    
    registry = ConfigRegistry(schema=schema)
    registry.load()
    
    model = ConfigurationModel(registry)
    value = model.get_bool("test.key")
    
    if not isinstance(value, bool):
        errmsg = f"Expected bool, got {type(value).__name__}"
        raise AssertionError(errmsg)
    
    if value is not True:
        errmsg = f"Expected True, got {value}"
        raise AssertionError(errmsg)
    
    return


def test_get_bool_coerces_string_to_bool():
    """
        Test that get_bool() coerces a string to boolean.
    """
    schema = ConfigSchema()
    schema.define("test.key", str, default="true")
    
    registry = ConfigRegistry(schema=schema)
    registry.load()
    
    model = ConfigurationModel(registry)
    value = model.get_bool("test.key")
    
    if not isinstance(value, bool):
        errmsg = f"Expected bool, got {type(value).__name__}"
        raise AssertionError(errmsg)
    
    if value is not True:
        errmsg = f"Expected True, got {value}"
        raise AssertionError(errmsg)
    
    return


def test_get_list_returns_list():
    """
        Test that get_list() returns a list value.
    """
    schema = ConfigSchema()
    schema.define("test.key", list, default=[1, 2, 3])
    
    registry = ConfigRegistry(schema=schema)
    registry.load()
    
    model = ConfigurationModel(registry)
    value = model.get_list("test.key")
    
    if not isinstance(value, list):
        errmsg = f"Expected list, got {type(value).__name__}"
        raise AssertionError(errmsg)
    
    if value != [1, 2, 3]:
        errmsg = f"Expected [1, 2, 3], got {value}"
        raise AssertionError(errmsg)
    
    return


def test_get_dict_returns_dict():
    """
        Test that get_dict() returns a dictionary value.
    """
    schema = ConfigSchema()
    schema.define("test.key", dict, default={"a": 1, "b": 2})
    
    registry = ConfigRegistry(schema=schema)
    registry.load()
    
    model = ConfigurationModel(registry)
    value = model.get_dict("test.key")
    
    if not isinstance(value, dict):
        errmsg = f"Expected dict, got {type(value).__name__}"
        raise AssertionError(errmsg)
    
    if value != {"a": 1, "b": 2}:
        errmsg = f"Expected {{'a': 1, 'b': 2}}, got {value}"
        raise AssertionError(errmsg)
    
    return



# =============================================================================
# Property Tests
# =============================================================================

# Feature: configuration-system, Property 1: Typed Access Consistency
# *For any* configuration value and target type, when the value is retrieved
# using a typed accessor (get_str, get_int, get_bool, etc.), the returned value
# SHALL be of the declared type or a ConfigurationError SHALL be raised if
# coercion is not possible.
# **Validates: Requirements 1.2**

def test_property_1_typed_access_consistency():
    """
        Property 1: Typed Access Consistency
        
        For any configuration value and target type, when the value is retrieved
        using a typed accessor (get_str, get_int, get_bool, etc.), the returned
        value SHALL be of the declared type or a ConfigurationTypeError SHALL be
        raised if coercion is not possible.
        
        **Feature: configuration-system, Property 1: Typed Access Consistency**
        **Validates: Requirements 1.2**
    """
    iterations = 100
    
    for iteration in range(iterations):
        # Test string values
        str_value = generate_random_string()
        schema = ConfigSchema()
        schema.define("str.key", str, default=str_value)
        registry = ConfigRegistry(schema=schema)
        registry.load()
        model = ConfigurationModel(registry)
        
        result = model.get_str("str.key")
        if not isinstance(result, str):
            errmsg = f"Iteration {iteration}: get_str() returned {type(result).__name__}, expected str"
            raise AssertionError(errmsg)
        
        # Test integer values
        int_value = generate_random_int()
        schema = ConfigSchema()
        schema.define("int.key", int, default=int_value)
        registry = ConfigRegistry(schema=schema)
        registry.load()
        model = ConfigurationModel(registry)
        
        result = model.get_int("int.key")
        if not isinstance(result, int):
            errmsg = f"Iteration {iteration}: get_int() returned {type(result).__name__}, expected int"
            raise AssertionError(errmsg)
        
        # Test float values
        float_value = generate_random_float()
        schema = ConfigSchema()
        schema.define("float.key", float, default=float_value)
        registry = ConfigRegistry(schema=schema)
        registry.load()
        model = ConfigurationModel(registry)
        
        result = model.get_float("float.key")
        if not isinstance(result, float):
            errmsg = f"Iteration {iteration}: get_float() returned {type(result).__name__}, expected float"
            raise AssertionError(errmsg)
        
        # Test boolean values
        bool_value = generate_random_bool()
        schema = ConfigSchema()
        schema.define("bool.key", bool, default=bool_value)
        registry = ConfigRegistry(schema=schema)
        registry.load()
        model = ConfigurationModel(registry)
        
        result = model.get_bool("bool.key")
        if not isinstance(result, bool):
            errmsg = f"Iteration {iteration}: get_bool() returned {type(result).__name__}, expected bool"
            raise AssertionError(errmsg)
        
        # Test list values
        list_value = generate_random_list()
        schema = ConfigSchema()
        schema.define("list.key", list, default=list_value)
        registry = ConfigRegistry(schema=schema)
        registry.load()
        model = ConfigurationModel(registry)
        
        result = model.get_list("list.key")
        if not isinstance(result, list):
            errmsg = f"Iteration {iteration}: get_list() returned {type(result).__name__}, expected list"
            raise AssertionError(errmsg)
        
        # Test dict values
        dict_value = generate_random_dict()
        schema = ConfigSchema()
        schema.define("dict.key", dict, default=dict_value)
        registry = ConfigRegistry(schema=schema)
        registry.load()
        model = ConfigurationModel(registry)
        
        result = model.get_dict("dict.key")
        if not isinstance(result, dict):
            errmsg = f"Iteration {iteration}: get_dict() returned {type(result).__name__}, expected dict"
            raise AssertionError(errmsg)
    
    return


def test_property_1_typed_access_coercion():
    """
        Property 1: Typed Access Consistency - Coercion
        
        For any string value that can be coerced to a target type, the typed
        accessor SHALL return the coerced value of the correct type.
        
        **Feature: configuration-system, Property 1: Typed Access Consistency**
        **Validates: Requirements 1.2**
    """
    iterations = 100
    
    for iteration in range(iterations):
        # Test string to int coercion
        int_value = generate_random_int()
        str_int = str(int_value)
        schema = ConfigSchema()
        schema.define("test.key", str, default=str_int)
        registry = ConfigRegistry(schema=schema)
        registry.load()
        model = ConfigurationModel(registry)
        
        result = model.get_int("test.key")
        if not isinstance(result, int):
            errmsg = f"Iteration {iteration}: get_int() on string '{str_int}' returned {type(result).__name__}"
            raise AssertionError(errmsg)
        if result != int_value:
            errmsg = f"Iteration {iteration}: get_int() returned {result}, expected {int_value}"
            raise AssertionError(errmsg)
        
        # Test string to float coercion
        float_value = round(generate_random_float(), 4)
        str_float = str(float_value)
        schema = ConfigSchema()
        schema.define("test.key", str, default=str_float)
        registry = ConfigRegistry(schema=schema)
        registry.load()
        model = ConfigurationModel(registry)
        
        result = model.get_float("test.key")
        if not isinstance(result, float):
            errmsg = f"Iteration {iteration}: get_float() on string '{str_float}' returned {type(result).__name__}"
            raise AssertionError(errmsg)
        if abs(result - float_value) > 0.0001:
            errmsg = f"Iteration {iteration}: get_float() returned {result}, expected {float_value}"
            raise AssertionError(errmsg)
        
        # Test string to bool coercion
        bool_strings = [
            ("true", True), ("false", False),
            ("yes", True), ("no", False),
            ("1", True), ("0", False),
            ("on", True), ("off", False)
        ]
        str_bool, expected_bool = random.choice(bool_strings)
        schema = ConfigSchema()
        schema.define("test.key", str, default=str_bool)
        registry = ConfigRegistry(schema=schema)
        registry.load()
        model = ConfigurationModel(registry)
        
        result = model.get_bool("test.key")
        if not isinstance(result, bool):
            errmsg = f"Iteration {iteration}: get_bool() on string '{str_bool}' returned {type(result).__name__}"
            raise AssertionError(errmsg)
        if result is not expected_bool:
            errmsg = f"Iteration {iteration}: get_bool('{str_bool}') returned {result}, expected {expected_bool}"
            raise AssertionError(errmsg)
    
    return



# =============================================================================
# Unit Tests for Dot-Notation and Dictionary Access
# =============================================================================

def test_dot_notation_access():
    """
        Test that dot-notation access works for configuration values.
    """
    schema = ConfigSchema()
    schema.define("database.host", str, default="localhost")
    schema.define("database.port", int, default=5432)
    
    registry = ConfigRegistry(schema=schema)
    registry.load()
    
    model = ConfigurationModel(registry)
    
    # Access via dot notation
    db = model.database
    if not isinstance(db, ConfigNamespace):
        errmsg = f"Expected ConfigNamespace, got {type(db).__name__}"
        raise AssertionError(errmsg)
    
    host = db.host
    if host != "localhost":
        errmsg = f"Expected 'localhost', got {host}"
        raise AssertionError(errmsg)
    
    port = db.port
    if port != 5432:
        errmsg = f"Expected 5432, got {port}"
        raise AssertionError(errmsg)
    
    return


def test_dictionary_access():
    """
        Test that dictionary-style access works for configuration values.
    """
    schema = ConfigSchema()
    schema.define("database.host", str, default="localhost")
    schema.define("database.port", int, default=5432)
    
    registry = ConfigRegistry(schema=schema)
    registry.load()
    
    model = ConfigurationModel(registry)
    
    # Access via dictionary notation
    db = model["database"]
    if not isinstance(db, ConfigNamespace):
        errmsg = f"Expected ConfigNamespace, got {type(db).__name__}"
        raise AssertionError(errmsg)
    
    host = db["host"]
    if host != "localhost":
        errmsg = f"Expected 'localhost', got {host}"
        raise AssertionError(errmsg)
    
    port = db["port"]
    if port != 5432:
        errmsg = f"Expected 5432, got {port}"
        raise AssertionError(errmsg)
    
    return


def test_dot_notation_raises_attribute_error():
    """
        Test that dot-notation access raises AttributeError for missing keys.
    """
    registry = ConfigRegistry()
    registry.load()
    
    model = ConfigurationModel(registry)
    
    try:
        _ = model.nonexistent
        errmsg = "Expected AttributeError to be raised"
        raise AssertionError(errmsg)
    except AttributeError as e:
        if "nonexistent" not in str(e):
            errmsg = f"Expected key name in error message, got {str(e)}"
            raise AssertionError(errmsg)
    
    return


def test_dictionary_access_raises_key_error():
    """
        Test that dictionary-style access raises KeyError for missing keys.
    """
    registry = ConfigRegistry()
    registry.load()
    
    model = ConfigurationModel(registry)
    
    try:
        _ = model["nonexistent"]
        errmsg = "Expected KeyError to be raised"
        raise AssertionError(errmsg)
    except KeyError as e:
        if "nonexistent" not in str(e):
            errmsg = f"Expected key name in error message, got {str(e)}"
            raise AssertionError(errmsg)
    
    return


# Feature: configuration-system, Property 2: Access Method Equivalence
# *For any* configuration key, accessing the value via dot-notation
# (config.database.host), dictionary-style (config["database"]["host"]),
# and get method (config.get("database.host")) SHALL return the same value.
# **Validates: Requirements 1.3, 1.4**

def test_property_2_access_method_equivalence():
    """
        Property 2: Access Method Equivalence
        
        For any configuration key, accessing the value via dot-notation
        (config.database.host), dictionary-style (config["database"]["host"]),
        and get method (config.get("database.host")) SHALL return the same value.
        
        **Feature: configuration-system, Property 2: Access Method Equivalence**
        **Validates: Requirements 1.3, 1.4**
    """
    iterations = 100
    
    for iteration in range(iterations):
        # Generate random configuration structure
        section = generate_random_string(3, 10).lower()
        key = generate_random_string(3, 10).lower()
        full_key = f"{section}.{key}"
        
        # Generate random value
        value_type = random.choice([str, int, float, bool])
        if value_type == str:
            value = generate_random_string()
        elif value_type == int:
            value = generate_random_int()
        elif value_type == float:
            value = generate_random_float()
        else:
            value = generate_random_bool()
        
        # Create schema and registry
        schema = ConfigSchema()
        schema.define(full_key, value_type, default=value)
        registry = ConfigRegistry(schema=schema)
        registry.load()
        model = ConfigurationModel(registry)
        
        # Access via get method
        get_value = model.get(full_key)
        
        # Access via dictionary notation
        dict_namespace = model[section]
        dict_value = dict_namespace[key]
        
        # Access via dot notation
        dot_namespace = getattr(model, section)
        dot_value = getattr(dot_namespace, key)
        
        # All three should be equal
        if get_value != dict_value:
            errmsg = f"Iteration {iteration}: get() returned {get_value}, dict access returned {dict_value}"
            raise AssertionError(errmsg)
        
        if get_value != dot_value:
            errmsg = f"Iteration {iteration}: get() returned {get_value}, dot access returned {dot_value}"
            raise AssertionError(errmsg)
    
    return


def test_property_2_nested_access_equivalence():
    """
        Property 2: Access Method Equivalence - Nested Keys
        
        For any deeply nested configuration key, all access methods SHALL
        return the same value.
        
        **Feature: configuration-system, Property 2: Access Method Equivalence**
        **Validates: Requirements 1.3, 1.4**
    """
    iterations = 100
    
    for iteration in range(iterations):
        # Generate random 3-level nested key
        level1 = generate_random_string(3, 8).lower()
        level2 = generate_random_string(3, 8).lower()
        level3 = generate_random_string(3, 8).lower()
        full_key = f"{level1}.{level2}.{level3}"
        
        value = generate_random_string()
        
        # Create schema and registry
        schema = ConfigSchema()
        schema.define(full_key, str, default=value)
        registry = ConfigRegistry(schema=schema)
        registry.load()
        model = ConfigurationModel(registry)
        
        # Access via get method
        get_value = model.get(full_key)
        
        # Access via dictionary notation
        dict_value = model[level1][level2][level3]
        
        # Access via dot notation
        dot_value = getattr(getattr(getattr(model, level1), level2), level3)
        
        # All three should be equal
        if get_value != dict_value:
            errmsg = f"Iteration {iteration}: get() returned {get_value}, dict access returned {dict_value}"
            raise AssertionError(errmsg)
        
        if get_value != dot_value:
            errmsg = f"Iteration {iteration}: get() returned {get_value}, dot access returned {dot_value}"
            raise AssertionError(errmsg)
    
    return



# =============================================================================
# Unit Tests for Default Value Handling
# =============================================================================

def test_get_returns_schema_default():
    """
        Test that get() returns the schema default when key not in sources.
    """
    schema = ConfigSchema()
    schema.define("test.key", str, default="schema_default")
    
    registry = ConfigRegistry(schema=schema)
    registry.load()
    
    model = ConfigurationModel(registry)
    value = model.get("test.key")
    
    if value != "schema_default":
        errmsg = f"Expected 'schema_default', got {value}"
        raise AssertionError(errmsg)
    
    return


def test_get_returns_provided_default_over_schema():
    """
        Test that get() returns the provided default when key not found.
    """
    schema = ConfigSchema()
    schema.define("test.key", str, default="schema_default")
    
    registry = ConfigRegistry(schema=schema)
    registry.load()
    
    model = ConfigurationModel(registry)
    # Access a key that doesn't exist in schema
    value = model.get("nonexistent.key", "provided_default")
    
    if value != "provided_default":
        errmsg = f"Expected 'provided_default', got {value}"
        raise AssertionError(errmsg)
    
    return


def test_get_returns_none_default():
    """
        Test that get() can return None as a default value.
    """
    registry = ConfigRegistry()
    registry.load()
    
    model = ConfigurationModel(registry)
    value = model.get("nonexistent.key", None)
    
    if value is not None:
        errmsg = f"Expected None, got {value}"
        raise AssertionError(errmsg)
    
    return


# Feature: configuration-system, Property 3: Default Value Resolution
# *For any* configuration key that is not present in any source, when a default
# value is specified in the access call, the default value SHALL be returned.
# **Validates: Requirements 1.5**

def test_property_3_default_value_resolution():
    """
        Property 3: Default Value Resolution
        
        For any configuration key that is not present in any source, when a
        default value is specified in the access call, the default value SHALL
        be returned.
        
        **Feature: configuration-system, Property 3: Default Value Resolution**
        **Validates: Requirements 1.5**
    """
    iterations = 100
    
    for iteration in range(iterations):
        # Generate random key that won't exist
        nonexistent_key = f"nonexistent.{generate_random_string(5, 10)}.{generate_random_string(5, 10)}"
        
        # Generate random default value
        value_type = random.choice([str, int, float, bool, list, dict])
        if value_type == str:
            default_value = generate_random_string()
        elif value_type == int:
            default_value = generate_random_int()
        elif value_type == float:
            default_value = generate_random_float()
        elif value_type == bool:
            default_value = generate_random_bool()
        elif value_type == list:
            default_value = generate_random_list()
        else:
            default_value = generate_random_dict()
        
        # Create empty registry (no sources)
        registry = ConfigRegistry()
        registry.load()
        model = ConfigurationModel(registry)
        
        # Access with default
        result = model.get(nonexistent_key, default_value)
        
        # Should return the provided default
        if result != default_value:
            errmsg = f"Iteration {iteration}: Expected default {default_value}, got {result}"
            raise AssertionError(errmsg)
    
    return


def test_property_3_schema_default_resolution():
    """
        Property 3: Default Value Resolution - Schema Defaults
        
        For any configuration key with a schema default, when the key is not
        present in any source, the schema default SHALL be returned.
        
        **Feature: configuration-system, Property 3: Default Value Resolution**
        **Validates: Requirements 1.5**
    """
    iterations = 100
    
    for iteration in range(iterations):
        # Generate random key
        key = f"{generate_random_string(3, 8)}.{generate_random_string(3, 8)}"
        
        # Generate random default value
        value_type = random.choice([str, int, float, bool])
        if value_type == str:
            default_value = generate_random_string()
        elif value_type == int:
            default_value = generate_random_int()
        elif value_type == float:
            default_value = generate_random_float()
        else:
            default_value = generate_random_bool()
        
        # Create schema with default
        schema = ConfigSchema()
        schema.define(key, value_type, default=default_value)
        
        # Create registry with schema but no sources
        registry = ConfigRegistry(schema=schema)
        registry.load()
        model = ConfigurationModel(registry)
        
        # Access without providing default
        result = model.get(key)
        
        # Should return the schema default
        if result != default_value:
            errmsg = f"Iteration {iteration}: Expected schema default {default_value}, got {result}"
            raise AssertionError(errmsg)
    
    return



# =============================================================================
# Unit Tests for Missing Required Key Error
# =============================================================================

def test_get_raises_error_for_required_key():
    """
        Test that get() raises ConfigurationError for missing required key.
    """
    schema = ConfigSchema()
    schema.define("required.key", str, required=True)
    
    registry = ConfigRegistry(schema=schema)
    # Don't validate on load to avoid validation error
    registry.load(validate=False)
    
    model = ConfigurationModel(registry)
    
    try:
        model.get("required.key")
        errmsg = "Expected ConfigurationError to be raised"
        raise AssertionError(errmsg)
    except ConfigurationError as e:
        if "required.key" not in str(e):
            errmsg = f"Expected key name in error message, got {str(e)}"
            raise AssertionError(errmsg)
    
    return


def test_get_raises_error_for_nonexistent_key_without_default():
    """
        Test that get() raises ConfigurationError for nonexistent key without default.
    """
    registry = ConfigRegistry()
    registry.load()
    
    model = ConfigurationModel(registry)
    
    try:
        model.get("nonexistent.key")
        errmsg = "Expected ConfigurationError to be raised"
        raise AssertionError(errmsg)
    except ConfigurationError as e:
        if "nonexistent.key" not in str(e):
            errmsg = f"Expected key name in error message, got {str(e)}"
            raise AssertionError(errmsg)
    
    return


# Feature: configuration-system, Property 4: Missing Required Key Error
# *For any* configuration key that is marked as required in the schema and is
# not present in any source, accessing that key without a default SHALL raise
# ConfigurationError.
# **Validates: Requirements 1.6**

def test_property_4_missing_required_key_error():
    """
        Property 4: Missing Required Key Error
        
        For any configuration key that is marked as required in the schema and
        is not present in any source, accessing that key without a default SHALL
        raise ConfigurationError.
        
        **Feature: configuration-system, Property 4: Missing Required Key Error**
        **Validates: Requirements 1.6**
    """
    iterations = 100
    
    for iteration in range(iterations):
        # Generate random required key
        key = f"{generate_random_string(3, 8)}.{generate_random_string(3, 8)}"
        
        # Create schema with required key
        schema = ConfigSchema()
        schema.define(key, str, required=True)
        
        # Create registry with schema but no sources
        registry = ConfigRegistry(schema=schema)
        # Don't validate on load to avoid validation error
        registry.load(validate=False)
        model = ConfigurationModel(registry)
        
        # Access without default should raise error
        error_raised = False
        try:
            model.get(key)
        except ConfigurationError as e:
            error_raised = True
            if key not in str(e):
                errmsg = f"Iteration {iteration}: Expected key '{key}' in error message, got {str(e)}"
                raise AssertionError(errmsg)
        
        if not error_raised:
            errmsg = f"Iteration {iteration}: Expected ConfigurationError for required key '{key}'"
            raise AssertionError(errmsg)
    
    return


def test_property_4_missing_key_error_without_schema():
    """
        Property 4: Missing Required Key Error - Without Schema
        
        For any configuration key that is not present in any source and no
        schema is defined, accessing that key without a default SHALL raise
        ConfigurationError.
        
        **Feature: configuration-system, Property 4: Missing Required Key Error**
        **Validates: Requirements 1.6**
    """
    iterations = 100
    
    for iteration in range(iterations):
        # Generate random nonexistent key
        key = f"nonexistent.{generate_random_string(5, 10)}.{generate_random_string(5, 10)}"
        
        # Create empty registry (no schema, no sources)
        registry = ConfigRegistry()
        registry.load()
        model = ConfigurationModel(registry)
        
        # Access without default should raise error
        error_raised = False
        try:
            model.get(key)
        except ConfigurationError as e:
            error_raised = True
            if key not in str(e):
                errmsg = f"Iteration {iteration}: Expected key '{key}' in error message, got {str(e)}"
                raise AssertionError(errmsg)
        
        if not error_raised:
            errmsg = f"Iteration {iteration}: Expected ConfigurationError for missing key '{key}'"
            raise AssertionError(errmsg)
    
    return



# =============================================================================
# Unit Tests for Metadata Access
# =============================================================================

def test_get_metadata_returns_metadata():
    """
        Test that get_metadata() returns ConfigValueMetadata.
    """
    schema = ConfigSchema()
    schema.define("test.key", str, default="value", description="Test key")
    
    registry = ConfigRegistry(schema=schema)
    registry.load()
    
    model = ConfigurationModel(registry)
    metadata = model.get_metadata("test.key")
    
    if not isinstance(metadata, ConfigValueMetadata):
        errmsg = f"Expected ConfigValueMetadata, got {type(metadata).__name__}"
        raise AssertionError(errmsg)
    
    return


def test_get_metadata_includes_source():
    """
        Test that get_metadata() includes source information.
    """
    schema = ConfigSchema()
    schema.define("test.key", str, default="value")
    
    registry = ConfigRegistry(schema=schema)
    registry.load()
    
    model = ConfigurationModel(registry)
    metadata = model.get_metadata("test.key")
    
    if metadata.source != ConfigSourceType.DEFAULT:
        errmsg = f"Expected source DEFAULT, got {metadata.source}"
        raise AssertionError(errmsg)
    
    return


def test_get_metadata_includes_schema_info():
    """
        Test that get_metadata() includes schema information.
    """
    schema = ConfigSchema()
    schema.define("test.key", str, default="default_value", description="Test description")
    
    registry = ConfigRegistry(schema=schema)
    registry.load()
    
    model = ConfigurationModel(registry)
    metadata = model.get_metadata("test.key")
    
    if metadata.schema_type is not str:
        errmsg = f"Expected schema_type str, got {metadata.schema_type}"
        raise AssertionError(errmsg)
    
    if metadata.schema_default != "default_value":
        errmsg = f"Expected schema_default 'default_value', got {metadata.schema_default}"
        raise AssertionError(errmsg)
    
    if metadata.schema_description != "Test description":
        errmsg = f"Expected schema_description 'Test description', got {metadata.schema_description}"
        raise AssertionError(errmsg)
    
    return


def test_get_metadata_for_override():
    """
        Test that get_metadata() correctly identifies overrides.
    """
    schema = ConfigSchema()
    schema.define("test.key", str, default="default_value")
    
    registry = ConfigRegistry(schema=schema)
    registry.load()
    registry.override("test.key", "override_value")
    
    model = ConfigurationModel(registry)
    metadata = model.get_metadata("test.key")
    
    if metadata.source != ConfigSourceType.OVERRIDE:
        errmsg = f"Expected source OVERRIDE, got {metadata.source}"
        raise AssertionError(errmsg)
    
    if metadata.is_override is not True:
        errmsg = f"Expected is_override True, got {metadata.is_override}"
        raise AssertionError(errmsg)
    
    return


def test_get_metadata_raises_error_for_missing_key():
    """
        Test that get_metadata() raises ConfigurationError for missing key.
    """
    registry = ConfigRegistry()
    registry.load()
    
    model = ConfigurationModel(registry)
    
    try:
        model.get_metadata("nonexistent.key")
        errmsg = "Expected ConfigurationError to be raised"
        raise AssertionError(errmsg)
    except ConfigurationError as e:
        if "nonexistent.key" not in str(e):
            errmsg = f"Expected key name in error message, got {str(e)}"
            raise AssertionError(errmsg)
    
    return


# Feature: configuration-system, Property 5: Value Source Metadata
# *For any* configuration value, the metadata SHALL accurately reflect the
# source from which the value was loaded and whether it was overridden.
# **Validates: Requirements 1.8**

def test_property_5_value_source_metadata():
    """
        Property 5: Value Source Metadata
        
        For any configuration value, the metadata SHALL accurately reflect the
        source from which the value was loaded and whether it was overridden.
        
        **Feature: configuration-system, Property 5: Value Source Metadata**
        **Validates: Requirements 1.8**
    """
    iterations = 100
    
    for iteration in range(iterations):
        # Generate random key
        key = f"{generate_random_string(3, 8)}.{generate_random_string(3, 8)}"
        value = generate_random_string()
        description = generate_random_string(10, 30)
        
        # Create schema with key
        schema = ConfigSchema()
        schema.define(key, str, default=value, description=description)
        
        # Create registry
        registry = ConfigRegistry(schema=schema)
        registry.load()
        model = ConfigurationModel(registry)
        
        # Get metadata
        metadata = model.get_metadata(key)
        
        # Verify source is DEFAULT (since value comes from schema default)
        if metadata.source != ConfigSourceType.DEFAULT:
            errmsg = f"Iteration {iteration}: Expected source DEFAULT, got {metadata.source}"
            raise AssertionError(errmsg)
        
        # Verify is_override is False
        if metadata.is_override is not False:
            errmsg = f"Iteration {iteration}: Expected is_override False, got {metadata.is_override}"
            raise AssertionError(errmsg)
        
        # Verify schema info
        if metadata.schema_type is not str:
            errmsg = f"Iteration {iteration}: Expected schema_type str, got {metadata.schema_type}"
            raise AssertionError(errmsg)
        
        if metadata.schema_default != value:
            errmsg = f"Iteration {iteration}: Expected schema_default '{value}', got {metadata.schema_default}"
            raise AssertionError(errmsg)
        
        if metadata.schema_description != description:
            errmsg = f"Iteration {iteration}: Expected schema_description '{description}', got {metadata.schema_description}"
            raise AssertionError(errmsg)
    
    return


def test_property_5_override_metadata():
    """
        Property 5: Value Source Metadata - Overrides
        
        For any configuration value that has been overridden, the metadata SHALL
        reflect the OVERRIDE source and is_override=True.
        
        **Feature: configuration-system, Property 5: Value Source Metadata**
        **Validates: Requirements 1.8**
    """
    iterations = 100
    
    for iteration in range(iterations):
        # Generate random key
        key = f"{generate_random_string(3, 8)}.{generate_random_string(3, 8)}"
        default_value = generate_random_string()
        override_value = generate_random_string()
        
        # Create schema with key
        schema = ConfigSchema()
        schema.define(key, str, default=default_value)
        
        # Create registry and override
        registry = ConfigRegistry(schema=schema)
        registry.load()
        registry.override(key, override_value)
        model = ConfigurationModel(registry)
        
        # Get metadata
        metadata = model.get_metadata(key)
        
        # Verify source is OVERRIDE
        if metadata.source != ConfigSourceType.OVERRIDE:
            errmsg = f"Iteration {iteration}: Expected source OVERRIDE, got {metadata.source}"
            raise AssertionError(errmsg)
        
        # Verify is_override is True
        if metadata.is_override is not True:
            errmsg = f"Iteration {iteration}: Expected is_override True, got {metadata.is_override}"
            raise AssertionError(errmsg)
        
        # Verify the actual value is the override
        actual_value = model.get(key)
        if actual_value != override_value:
            errmsg = f"Iteration {iteration}: Expected value '{override_value}', got {actual_value}"
            raise AssertionError(errmsg)
    
    return



# =============================================================================
# Unit Tests for Namespace Grouping
# =============================================================================

def test_namespace_returns_config_namespace():
    """
        Test that namespace() returns a ConfigNamespace.
    """
    schema = ConfigSchema()
    schema.define("database.host", str, default="localhost")
    
    registry = ConfigRegistry(schema=schema)
    registry.load()
    
    model = ConfigurationModel(registry)
    ns = model.namespace("database")
    
    if not isinstance(ns, ConfigNamespace):
        errmsg = f"Expected ConfigNamespace, got {type(ns).__name__}"
        raise AssertionError(errmsg)
    
    return


def test_namespace_prefix():
    """
        Test that ConfigNamespace has the correct prefix.
    """
    schema = ConfigSchema()
    schema.define("database.host", str, default="localhost")
    
    registry = ConfigRegistry(schema=schema)
    registry.load()
    
    model = ConfigurationModel(registry)
    ns = model.namespace("database")
    
    if ns.prefix != "database":
        errmsg = f"Expected prefix 'database', got {ns.prefix}"
        raise AssertionError(errmsg)
    
    return


def test_namespace_get():
    """
        Test that ConfigNamespace.get() works correctly.
    """
    schema = ConfigSchema()
    schema.define("database.host", str, default="localhost")
    schema.define("database.port", int, default=5432)
    
    registry = ConfigRegistry(schema=schema)
    registry.load()
    
    model = ConfigurationModel(registry)
    db = model.namespace("database")
    
    host = db.get("host")
    if host != "localhost":
        errmsg = f"Expected 'localhost', got {host}"
        raise AssertionError(errmsg)
    
    port = db.get("port")
    if port != 5432:
        errmsg = f"Expected 5432, got {port}"
        raise AssertionError(errmsg)
    
    return


def test_namespace_typed_access():
    """
        Test that ConfigNamespace typed access methods work correctly.
    """
    schema = ConfigSchema()
    schema.define("database.host", str, default="localhost")
    schema.define("database.port", int, default=5432)
    schema.define("database.enabled", bool, default=True)
    
    registry = ConfigRegistry(schema=schema)
    registry.load()
    
    model = ConfigurationModel(registry)
    db = model.namespace("database")
    
    host = db.get_str("host")
    if not isinstance(host, str) or host != "localhost":
        errmsg = f"Expected str 'localhost', got {type(host).__name__} {host}"
        raise AssertionError(errmsg)
    
    port = db.get_int("port")
    if not isinstance(port, int) or port != 5432:
        errmsg = f"Expected int 5432, got {type(port).__name__} {port}"
        raise AssertionError(errmsg)
    
    enabled = db.get_bool("enabled")
    if not isinstance(enabled, bool) or enabled is not True:
        errmsg = f"Expected bool True, got {type(enabled).__name__} {enabled}"
        raise AssertionError(errmsg)
    
    return


def test_namespace_nested():
    """
        Test that ConfigNamespace.namespace() creates nested namespaces.
    """
    schema = ConfigSchema()
    schema.define("database.connection.host", str, default="localhost")
    schema.define("database.connection.port", int, default=5432)
    
    registry = ConfigRegistry(schema=schema)
    registry.load()
    
    model = ConfigurationModel(registry)
    db = model.namespace("database")
    conn = db.namespace("connection")
    
    if not isinstance(conn, ConfigNamespace):
        errmsg = f"Expected ConfigNamespace, got {type(conn).__name__}"
        raise AssertionError(errmsg)
    
    if conn.prefix != "database.connection":
        errmsg = f"Expected prefix 'database.connection', got {conn.prefix}"
        raise AssertionError(errmsg)
    
    host = conn.get("host")
    if host != "localhost":
        errmsg = f"Expected 'localhost', got {host}"
        raise AssertionError(errmsg)
    
    return


def test_namespace_get_metadata():
    """
        Test that ConfigNamespace.get_metadata() works correctly.
    """
    schema = ConfigSchema()
    schema.define("database.host", str, default="localhost", description="Database host")
    
    registry = ConfigRegistry(schema=schema)
    registry.load()
    
    model = ConfigurationModel(registry)
    db = model.namespace("database")
    
    metadata = db.get_metadata("host")
    
    if not isinstance(metadata, ConfigValueMetadata):
        errmsg = f"Expected ConfigValueMetadata, got {type(metadata).__name__}"
        raise AssertionError(errmsg)
    
    if metadata.schema_description != "Database host":
        errmsg = f"Expected description 'Database host', got {metadata.schema_description}"
        raise AssertionError(errmsg)
    
    return


def test_namespace_dot_notation():
    """
        Test that ConfigNamespace supports dot-notation access.
    """
    schema = ConfigSchema()
    schema.define("database.host", str, default="localhost")
    
    registry = ConfigRegistry(schema=schema)
    registry.load()
    
    model = ConfigurationModel(registry)
    db = model.namespace("database")
    
    host = db.host
    if host != "localhost":
        errmsg = f"Expected 'localhost', got {host}"
        raise AssertionError(errmsg)
    
    return


def test_namespace_dictionary_access():
    """
        Test that ConfigNamespace supports dictionary-style access.
    """
    schema = ConfigSchema()
    schema.define("database.host", str, default="localhost")
    
    registry = ConfigRegistry(schema=schema)
    registry.load()
    
    model = ConfigurationModel(registry)
    db = model.namespace("database")
    
    host = db["host"]
    if host != "localhost":
        errmsg = f"Expected 'localhost', got {host}"
        raise AssertionError(errmsg)
    
    return


def test_model_keys():
    """
        Test that ConfigurationModel.keys() returns all keys.
    """
    schema = ConfigSchema()
    schema.define("database.host", str, default="localhost")
    schema.define("database.port", int, default=5432)
    schema.define("logging.level", str, default="INFO")
    
    registry = ConfigRegistry(schema=schema)
    registry.load()
    
    model = ConfigurationModel(registry)
    keys = model.keys()
    
    if "database.host" not in keys:
        errmsg = "Expected 'database.host' in keys"
        raise AssertionError(errmsg)
    
    if "database.port" not in keys:
        errmsg = "Expected 'database.port' in keys"
        raise AssertionError(errmsg)
    
    if "logging.level" not in keys:
        errmsg = "Expected 'logging.level' in keys"
        raise AssertionError(errmsg)
    
    return


def test_model_items():
    """
        Test that ConfigurationModel.items() returns all key-value pairs.
    """
    schema = ConfigSchema()
    schema.define("database.host", str, default="localhost")
    schema.define("database.port", int, default=5432)
    
    registry = ConfigRegistry(schema=schema)
    registry.load()
    
    model = ConfigurationModel(registry)
    items = model.items()
    
    items_dict = dict(items)
    
    if items_dict.get("database.host") != "localhost":
        errmsg = f"Expected 'localhost' for database.host, got {items_dict.get('database.host')}"
        raise AssertionError(errmsg)
    
    if items_dict.get("database.port") != 5432:
        errmsg = f"Expected 5432 for database.port, got {items_dict.get('database.port')}"
        raise AssertionError(errmsg)
    
    return


def test_model_contains():
    """
        Test that ConfigurationModel supports 'in' operator.
    """
    schema = ConfigSchema()
    schema.define("database.host", str, default="localhost")
    
    registry = ConfigRegistry(schema=schema)
    registry.load()
    
    model = ConfigurationModel(registry)
    
    if "database.host" not in model:
        errmsg = "Expected 'database.host' to be in model"
        raise AssertionError(errmsg)
    
    if "nonexistent.key" in model:
        errmsg = "Expected 'nonexistent.key' to not be in model"
        raise AssertionError(errmsg)
    
    return


