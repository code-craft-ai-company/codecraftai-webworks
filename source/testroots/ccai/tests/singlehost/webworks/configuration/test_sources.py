"""
    Tests for the configuration sources module.
    
    This module contains unit tests and property-based tests for the
    ConfigSource abstract base class and EnvironmentSource implementation.
"""

import os
import random
import string
from typing import Dict

from ccai.webworks.configuration import (
    ConfigSource,
    ConfigSourceType,
    EnvironmentSource
)


# =============================================================================
# Helper Functions for Test Data Generation
# =============================================================================

def generate_random_key_part(min_length: int = 2, max_length: int = 10) -> str:
    """
        Generate a random key part (lowercase letters only).
        
        :param min_length: Minimum length.
        :param max_length: Maximum length.
        
        :returns: A random lowercase string.
    """
    length = random.randint(min_length, max_length)
    return ''.join(random.choice(string.ascii_lowercase) for _ in range(length))


def generate_random_config_key(num_parts: int = None) -> str:
    """
        Generate a random configuration key in dot-notation.
        
        :param num_parts: Number of parts (random 1-4 if not specified).
        
        :returns: A random key like "database.host" or "api.key".
    """
    if num_parts is None:
        num_parts = random.randint(1, 4)
    parts = [generate_random_key_part() for _ in range(num_parts)]
    return '.'.join(parts)


def generate_random_value() -> str:
    """
        Generate a random configuration value.
        
        :returns: A random string value.
    """
    length = random.randint(1, 50)
    chars = string.ascii_letters + string.digits + "_-."
    return ''.join(random.choice(chars) for _ in range(length))


def config_key_to_env_name(
    config_key: str,
    prefix: str = "APP_",
    separator: str = "_"
) -> str:
    """
        Convert a configuration key to an environment variable name.
        
        :param config_key: The configuration key (e.g., "database.host").
        :param prefix: The environment variable prefix.
        :param separator: The separator to use.
        
        :returns: The environment variable name (e.g., "APP_DATABASE_HOST").
    """
    env_name = config_key.replace(".", separator).upper()
    return prefix + env_name


def set_test_env_vars(env_vars: Dict[str, str]) -> None:
    """
        Set environment variables for testing.
        
        :param env_vars: Dictionary of environment variable names to values.
    """
    for name, value in env_vars.items():
        os.environ[name] = value


def clear_test_env_vars(env_vars: Dict[str, str]) -> None:
    """
        Clear environment variables after testing.
        
        :param env_vars: Dictionary of environment variable names to clear.
    """
    for name in env_vars.keys():
        if name in os.environ:
            del os.environ[name]


# =============================================================================
# Unit Tests for ConfigSource Abstract Base Class
# =============================================================================

def test_config_source_is_abstract():
    """
        Test that ConfigSource cannot be instantiated directly.
    """
    try:
        ConfigSource()
        errmsg = "ConfigSource should not be instantiable"
        raise AssertionError(errmsg)
    except TypeError:
        pass  # Expected - abstract class cannot be instantiated
    
    return


def test_config_source_subclass_must_implement_load():
    """
        Test that ConfigSource subclass must implement load().
    """
    class IncompleteSource(ConfigSource):
        @property
        def source_type(self) -> ConfigSourceType:
            return ConfigSourceType.FILE
    
    try:
        IncompleteSource()
        errmsg = "IncompleteSource should not be instantiable without load()"
        raise AssertionError(errmsg)
    except TypeError:
        pass  # Expected - abstract method not implemented
    
    return


def test_config_source_subclass_must_implement_source_type():
    """
        Test that ConfigSource subclass must implement source_type property.
    """
    class IncompleteSource(ConfigSource):
        def load(self) -> dict:
            return {}
    
    try:
        IncompleteSource()
        errmsg = "IncompleteSource should not be instantiable without source_type"
        raise AssertionError(errmsg)
    except TypeError:
        pass  # Expected - abstract property not implemented
    
    return


def test_config_source_complete_subclass():
    """
        Test that a complete ConfigSource subclass can be instantiated.
    """
    class CompleteSource(ConfigSource):
        def load(self) -> dict:
            return {"test.key": "test_value"}
        
        @property
        def source_type(self) -> ConfigSourceType:
            return ConfigSourceType.FILE
    
    source = CompleteSource()
    
    if source.source_type != ConfigSourceType.FILE:
        errmsg = f"Expected source_type FILE, got {source.source_type}"
        raise AssertionError(errmsg)
    
    result = source.load()
    if result != {"test.key": "test_value"}:
        errmsg = f"Expected {{'test.key': 'test_value'}}, got {result}"
        raise AssertionError(errmsg)
    
    return


# =============================================================================
# Unit Tests for EnvironmentSource
# =============================================================================

def test_environment_source_creation_defaults():
    """
        Test that EnvironmentSource can be created with default parameters.
    """
    source = EnvironmentSource()
    
    if source.prefix != "APP_":
        errmsg = f"Expected prefix 'APP_', got {source.prefix}"
        raise AssertionError(errmsg)
    
    if source.separator != "_":
        errmsg = f"Expected separator '_', got {source.separator}"
        raise AssertionError(errmsg)
    
    if source.lowercase_keys is not True:
        errmsg = f"Expected lowercase_keys True, got {source.lowercase_keys}"
        raise AssertionError(errmsg)
    
    return


def test_environment_source_creation_custom():
    """
        Test that EnvironmentSource can be created with custom parameters.
    """
    source = EnvironmentSource(
        prefix="MYAPP_",
        separator="__",
        lowercase_keys=False
    )
    
    if source.prefix != "MYAPP_":
        errmsg = f"Expected prefix 'MYAPP_', got {source.prefix}"
        raise AssertionError(errmsg)
    
    if source.separator != "__":
        errmsg = f"Expected separator '__', got {source.separator}"
        raise AssertionError(errmsg)
    
    if source.lowercase_keys is not False:
        errmsg = f"Expected lowercase_keys False, got {source.lowercase_keys}"
        raise AssertionError(errmsg)
    
    return


def test_environment_source_source_type():
    """
        Test that EnvironmentSource has correct source_type.
    """
    source = EnvironmentSource()
    
    if source.source_type != ConfigSourceType.ENVIRONMENT:
        errmsg = f"Expected source_type ENVIRONMENT, got {source.source_type}"
        raise AssertionError(errmsg)
    
    return


def test_environment_source_load_empty():
    """
        Test that EnvironmentSource.load() returns empty dict when no matching vars.
    """
    # Use a unique prefix that won't match any existing env vars
    source = EnvironmentSource(prefix="UNIQUE_TEST_PREFIX_12345_")
    
    result = source.load()
    
    if result != {}:
        errmsg = f"Expected empty dict, got {result}"
        raise AssertionError(errmsg)
    
    return


def test_environment_source_load_single_var():
    """
        Test that EnvironmentSource.load() loads a single environment variable.
    """
    env_vars = {"TEST_SINGLE_HOST": "localhost"}
    
    try:
        set_test_env_vars(env_vars)
        
        source = EnvironmentSource(prefix="TEST_SINGLE_")
        result = source.load()
        
        if "host" not in result:
            errmsg = f"Expected 'host' in result, got {result}"
            raise AssertionError(errmsg)
        
        if result["host"] != "localhost":
            errmsg = f"Expected 'localhost', got {result['host']}"
            raise AssertionError(errmsg)
    finally:
        clear_test_env_vars(env_vars)
    
    return


def test_environment_source_load_nested_key():
    """
        Test that EnvironmentSource.load() maps nested keys correctly.
    """
    env_vars = {"TEST_NESTED_DATABASE_HOST": "db.example.com"}
    
    try:
        set_test_env_vars(env_vars)
        
        source = EnvironmentSource(prefix="TEST_NESTED_")
        result = source.load()
        
        if "database.host" not in result:
            errmsg = f"Expected 'database.host' in result, got {result}"
            raise AssertionError(errmsg)
        
        if result["database.host"] != "db.example.com":
            errmsg = f"Expected 'db.example.com', got {result['database.host']}"
            raise AssertionError(errmsg)
    finally:
        clear_test_env_vars(env_vars)
    
    return


def test_environment_source_load_multiple_vars():
    """
        Test that EnvironmentSource.load() loads multiple environment variables.
    """
    env_vars = {
        "TEST_MULTI_DATABASE_HOST": "localhost",
        "TEST_MULTI_DATABASE_PORT": "5432",
        "TEST_MULTI_LOG_LEVEL": "DEBUG"
    }
    
    try:
        set_test_env_vars(env_vars)
        
        source = EnvironmentSource(prefix="TEST_MULTI_")
        result = source.load()
        
        if len(result) != 3:
            errmsg = f"Expected 3 keys, got {len(result)}: {result}"
            raise AssertionError(errmsg)
        
        if result.get("database.host") != "localhost":
            errmsg = f"Expected database.host='localhost', got {result.get('database.host')}"
            raise AssertionError(errmsg)
        
        if result.get("database.port") != "5432":
            errmsg = f"Expected database.port='5432', got {result.get('database.port')}"
            raise AssertionError(errmsg)
        
        if result.get("log.level") != "DEBUG":
            errmsg = f"Expected log.level='DEBUG', got {result.get('log.level')}"
            raise AssertionError(errmsg)
    finally:
        clear_test_env_vars(env_vars)
    
    return


def test_environment_source_load_ignores_non_prefixed():
    """
        Test that EnvironmentSource.load() ignores non-prefixed variables.
    """
    env_vars = {
        "TEST_IGNORE_DATABASE_HOST": "localhost",
        "OTHER_DATABASE_HOST": "other.example.com"
    }
    
    try:
        set_test_env_vars(env_vars)
        
        source = EnvironmentSource(prefix="TEST_IGNORE_")
        result = source.load()
        
        if len(result) != 1:
            errmsg = f"Expected 1 key, got {len(result)}: {result}"
            raise AssertionError(errmsg)
        
        if "database.host" not in result:
            errmsg = f"Expected 'database.host' in result, got {result}"
            raise AssertionError(errmsg)
        
        if result["database.host"] != "localhost":
            errmsg = f"Expected 'localhost', got {result['database.host']}"
            raise AssertionError(errmsg)
    finally:
        clear_test_env_vars(env_vars)
    
    return


def test_environment_source_load_custom_separator():
    """
        Test that EnvironmentSource.load() uses custom separator.
    """
    env_vars = {"TEST_SEP__DATABASE__HOST": "localhost"}
    
    try:
        set_test_env_vars(env_vars)
        
        source = EnvironmentSource(prefix="TEST_SEP__", separator="__")
        result = source.load()
        
        if "database.host" not in result:
            errmsg = f"Expected 'database.host' in result, got {result}"
            raise AssertionError(errmsg)
        
        if result["database.host"] != "localhost":
            errmsg = f"Expected 'localhost', got {result['database.host']}"
            raise AssertionError(errmsg)
    finally:
        clear_test_env_vars(env_vars)
    
    return


def test_environment_source_load_no_lowercase():
    """
        Test that EnvironmentSource.load() preserves case when lowercase_keys=False.
    """
    env_vars = {"TEST_CASE_DATABASE_HOST": "localhost"}
    
    try:
        set_test_env_vars(env_vars)
        
        source = EnvironmentSource(prefix="TEST_CASE_", lowercase_keys=False)
        result = source.load()
        
        if "DATABASE.HOST" not in result:
            errmsg = f"Expected 'DATABASE.HOST' in result, got {result}"
            raise AssertionError(errmsg)
        
        if result["DATABASE.HOST"] != "localhost":
            errmsg = f"Expected 'localhost', got {result['DATABASE.HOST']}"
            raise AssertionError(errmsg)
    finally:
        clear_test_env_vars(env_vars)
    
    return


def test_environment_source_transform_key_to_env_name():
    """
        Test that transform_key_to_env_name() works correctly.
    """
    source = EnvironmentSource(prefix="APP_", separator="_", lowercase_keys=True)
    
    env_name = source.transform_key_to_env_name("database.host")
    
    if env_name != "APP_DATABASE_HOST":
        errmsg = f"Expected 'APP_DATABASE_HOST', got {env_name}"
        raise AssertionError(errmsg)
    
    return


def test_environment_source_transform_key_to_env_name_custom():
    """
        Test that transform_key_to_env_name() works with custom settings.
    """
    source = EnvironmentSource(prefix="MYAPP__", separator="__", lowercase_keys=True)
    
    env_name = source.transform_key_to_env_name("database.host")
    
    if env_name != "MYAPP__DATABASE__HOST":
        errmsg = f"Expected 'MYAPP__DATABASE__HOST', got {env_name}"
        raise AssertionError(errmsg)
    
    return


def test_environment_source_deeply_nested_key():
    """
        Test that EnvironmentSource handles deeply nested keys.
    """
    env_vars = {"TEST_DEEP_A_B_C_D_E": "deep_value"}
    
    try:
        set_test_env_vars(env_vars)
        
        source = EnvironmentSource(prefix="TEST_DEEP_")
        result = source.load()
        
        if "a.b.c.d.e" not in result:
            errmsg = f"Expected 'a.b.c.d.e' in result, got {result}"
            raise AssertionError(errmsg)
        
        if result["a.b.c.d.e"] != "deep_value":
            errmsg = f"Expected 'deep_value', got {result['a.b.c.d.e']}"
            raise AssertionError(errmsg)
    finally:
        clear_test_env_vars(env_vars)
    
    return


# =============================================================================
# Property-Based Tests for Environment Variable Mapping
# =============================================================================

# Feature: configuration-system, Property 8: Environment Variable Mapping
# *For any* environment variable with the configured prefix, the variable SHALL
# be mapped to the correct configuration key using the configured separator and
# case transformation rules.
# **Validates: Requirements 2.10**

def test_property_8_environment_variable_mapping():
    """
        Property 8: Environment Variable Mapping
        
        For any environment variable with the configured prefix, the variable
        SHALL be mapped to the correct configuration key using the configured
        separator and case transformation rules.
        
        **Feature: configuration-system, Property 8: Environment Variable Mapping**
        **Validates: Requirements 2.10**
    """
    # Run 100 iterations with random data
    for iteration in range(100):
        # Generate a unique prefix for this iteration to avoid conflicts
        prefix = f"PROP8_ITER{iteration}_"
        separator = "_"
        
        # Generate random configuration keys and values
        num_keys = random.randint(1, 5)
        expected_config: Dict[str, str] = {}
        env_vars: Dict[str, str] = {}
        
        for _ in range(num_keys):
            # Generate a random config key
            config_key = generate_random_config_key()
            value = generate_random_value()
            
            # Convert to environment variable name
            env_name = config_key_to_env_name(config_key, prefix, separator)
            
            expected_config[config_key] = value
            env_vars[env_name] = value
        
        try:
            # Set the environment variables
            set_test_env_vars(env_vars)
            
            # Create source and load
            source = EnvironmentSource(prefix=prefix, separator=separator, lowercase_keys=True)
            result = source.load()
            
            # Verify all expected keys are present with correct values
            for config_key, expected_value in expected_config.items():
                if config_key not in result:
                    errmsg = f"Iteration {iteration}: Expected key '{config_key}' in result, got {result}"
                    raise AssertionError(errmsg)
                
                if result[config_key] != expected_value:
                    errmsg = f"Iteration {iteration}: Expected value '{expected_value}' for key '{config_key}', got '{result[config_key]}'"
                    raise AssertionError(errmsg)
            
            # Verify no extra keys
            if len(result) != len(expected_config):
                errmsg = f"Iteration {iteration}: Expected {len(expected_config)} keys, got {len(result)}"
                raise AssertionError(errmsg)
        
        finally:
            # Clean up environment variables
            clear_test_env_vars(env_vars)
    
    return


def test_property_8_environment_variable_mapping_round_trip():
    """
        Property 8 (Extended): Environment Variable Mapping Round-Trip
        
        For any configuration key, converting to an environment variable name
        and back should produce the original key (when lowercase_keys=True).
        
        **Feature: configuration-system, Property 8: Environment Variable Mapping**
        **Validates: Requirements 2.10**
    """
    # Run 100 iterations with random data
    for iteration in range(100):
        # Generate a random config key (lowercase since we're testing round-trip)
        config_key = generate_random_config_key()
        
        # Create source with default settings
        source = EnvironmentSource(prefix="APP_", separator="_", lowercase_keys=True)
        
        # Convert config key to env name
        env_name = source.transform_key_to_env_name(config_key)
        
        # Verify the env name has the correct format
        expected_env_name = "APP_" + config_key.replace(".", "_").upper()
        if env_name != expected_env_name:
            errmsg = f"Iteration {iteration}: Expected env name '{expected_env_name}', got '{env_name}'"
            raise AssertionError(errmsg)
        
        # Now set this env var and load to verify round-trip
        test_value = generate_random_value()
        env_vars = {env_name: test_value}
        
        try:
            set_test_env_vars(env_vars)
            result = source.load()
            
            if config_key not in result:
                errmsg = f"Iteration {iteration}: Expected key '{config_key}' in result after round-trip, got {result}"
                raise AssertionError(errmsg)
            
            if result[config_key] != test_value:
                errmsg = f"Iteration {iteration}: Expected value '{test_value}' after round-trip, got '{result[config_key]}'"
                raise AssertionError(errmsg)
        
        finally:
            clear_test_env_vars(env_vars)
    
    return


def test_property_8_environment_variable_mapping_custom_separator():
    """
        Property 8 (Extended): Environment Variable Mapping with Custom Separator
        
        For any environment variable with a custom separator, the variable
        SHALL be mapped correctly using that separator.
        
        **Feature: configuration-system, Property 8: Environment Variable Mapping**
        **Validates: Requirements 2.10**
    """
    # Test with various separators
    separators = ["_", "__", "-", ".", "::"]
    
    for sep_idx, separator in enumerate(separators):
        # Run 20 iterations per separator
        for iteration in range(20):
            prefix = f"PROP8SEP{sep_idx}ITER{iteration}{separator}"
            
            # Generate random config keys and values
            num_keys = random.randint(1, 3)
            expected_config: Dict[str, str] = {}
            env_vars: Dict[str, str] = {}
            
            for _ in range(num_keys):
                config_key = generate_random_config_key()
                value = generate_random_value()
                
                # Convert to environment variable name using custom separator
                env_name = prefix + config_key.replace(".", separator).upper()
                
                expected_config[config_key] = value
                env_vars[env_name] = value
            
            try:
                set_test_env_vars(env_vars)
                
                source = EnvironmentSource(prefix=prefix, separator=separator, lowercase_keys=True)
                result = source.load()
                
                for config_key, expected_value in expected_config.items():
                    if config_key not in result:
                        errmsg = f"Separator '{separator}', Iteration {iteration}: Expected key '{config_key}' in result, got {result}"
                        raise AssertionError(errmsg)
                    
                    if result[config_key] != expected_value:
                        errmsg = f"Separator '{separator}', Iteration {iteration}: Expected value '{expected_value}' for key '{config_key}', got '{result[config_key]}'"
                        raise AssertionError(errmsg)
            
            finally:
                clear_test_env_vars(env_vars)
    
    return


def test_property_8_environment_variable_mapping_case_preservation():
    """
        Property 8 (Extended): Environment Variable Mapping Case Preservation
        
        When lowercase_keys=False, the case of the environment variable name
        (after prefix removal) SHALL be preserved in the configuration key.
        
        **Feature: configuration-system, Property 8: Environment Variable Mapping**
        **Validates: Requirements 2.10**
    """
    # Run 100 iterations with random data
    for iteration in range(100):
        prefix = f"PROP8CASE{iteration}_"
        
        # Generate a random config key with mixed case
        parts = [generate_random_key_part().upper() for _ in range(random.randint(1, 3))]
        config_key_upper = '.'.join(parts)
        value = generate_random_value()
        
        # Create env var name (already uppercase)
        env_name = prefix + config_key_upper.replace(".", "_")
        env_vars = {env_name: value}
        
        try:
            set_test_env_vars(env_vars)
            
            # With lowercase_keys=False, the key should preserve case
            source = EnvironmentSource(prefix=prefix, separator="_", lowercase_keys=False)
            result = source.load()
            
            if config_key_upper not in result:
                errmsg = f"Iteration {iteration}: Expected key '{config_key_upper}' in result, got {result}"
                raise AssertionError(errmsg)
            
            if result[config_key_upper] != value:
                errmsg = f"Iteration {iteration}: Expected value '{value}', got '{result[config_key_upper]}'"
                raise AssertionError(errmsg)
        
        finally:
            clear_test_env_vars(env_vars)
    
    return


import tempfile
import shutil
from pathlib import Path
from typing import Any, List

from ccai.webworks.configuration import (
    ConfigLoader,
    IniLoader,
    JsonLoader,
    FileSource,
    ConfigurationError,
    ConfigurationFileNotFoundError,
    YAML_AVAILABLE,
    TOML_AVAILABLE
)

# Conditionally import YAML and TOML loaders
if YAML_AVAILABLE:
    from ccai.webworks.configuration import YamlLoader

if TOML_AVAILABLE:
    from ccai.webworks.configuration import TomlLoader


# =============================================================================
# Helper Functions for File-Based Tests
# =============================================================================

def generate_random_simple_value() -> Any:
    """
        Generate a random simple configuration value (string, int, or bool).
        
        :returns: A random value suitable for all config formats.
    """
    value_type = random.choice(["string", "int", "bool"])
    
    if value_type == "string":
        length = random.randint(1, 20)
        chars = string.ascii_letters + string.digits
        return ''.join(random.choice(chars) for _ in range(length))
    elif value_type == "int":
        return random.randint(0, 10000)
    else:
        return random.choice([True, False])


def generate_random_config_dict(num_keys: int = None, max_depth: int = 2) -> Dict[str, Any]:
    """
        Generate a random configuration dictionary with dot-notation keys.
        
        This function ensures no conflicting keys are generated (e.g., both
        'a' and 'a.b' would conflict because 'a' would need to be both a
        value and a parent object).
        
        :param num_keys: Number of keys (random 1-5 if not specified).
        :param max_depth: Maximum nesting depth.
        
        :returns: A dictionary with dot-notation keys and simple values.
    """
    if num_keys is None:
        num_keys = random.randint(1, 5)
    
    result: Dict[str, Any] = {}
    
    for _ in range(num_keys):
        # Generate a key with random depth
        depth = random.randint(1, max_depth)
        
        # Try to generate a non-conflicting key
        for _ in range(10):  # Max attempts
            key = generate_random_config_key(depth)
            
            # Check if this key conflicts with existing keys
            # A key conflicts if it's a prefix of an existing key or vice versa
            parts = key.split(".")
            has_conflict = False
            
            # Check if any prefix of this key is already a value
            for i in range(1, len(parts)):
                prefix = ".".join(parts[:i])
                if prefix in result:
                    has_conflict = True
                    break
            
            # Check if this key is a prefix of any existing key
            if not has_conflict:
                for existing_key in result:
                    if existing_key.startswith(key + "."):
                        has_conflict = True
                        break
            
            if not has_conflict:
                break
        
        if not has_conflict:
            value = generate_random_simple_value()
            result[key] = value
    
    return result


def normalize_config_values(config: Dict[str, Any]) -> Dict[str, str]:
    """
        Normalize configuration values to strings for comparison.
        
        INI format stores everything as strings, so we need to normalize
        for comparison.
        
        :param config: The configuration dictionary.
        
        :returns: Dictionary with all values as strings.
    """
    result: Dict[str, str] = {}
    for key, value in config.items():
        if isinstance(value, bool):
            result[key] = str(value).lower()
        else:
            result[key] = str(value)
    return result


# =============================================================================
# Unit Tests for ConfigLoader Abstract Base Class
# =============================================================================

def test_config_loader_is_abstract():
    """
        Test that ConfigLoader cannot be instantiated directly.
    """
    try:
        ConfigLoader()
        errmsg = "ConfigLoader should not be instantiable"
        raise AssertionError(errmsg)
    except TypeError:
        pass  # Expected - abstract class cannot be instantiated
    
    return


def test_config_loader_subclass_must_implement_load():
    """
        Test that ConfigLoader subclass must implement load().
    """
    class IncompleteLoader(ConfigLoader):
        def dump(self, data: dict) -> str:
            return ""
    
    try:
        IncompleteLoader()
        errmsg = "IncompleteLoader should not be instantiable without load()"
        raise AssertionError(errmsg)
    except TypeError:
        pass  # Expected - abstract method not implemented
    
    return


def test_config_loader_subclass_must_implement_dump():
    """
        Test that ConfigLoader subclass must implement dump().
    """
    class IncompleteLoader(ConfigLoader):
        def load(self, content: str) -> dict:
            return {}
    
    try:
        IncompleteLoader()
        errmsg = "IncompleteLoader should not be instantiable without dump()"
        raise AssertionError(errmsg)
    except TypeError:
        pass  # Expected - abstract method not implemented
    
    return


# =============================================================================
# Unit Tests for IniLoader
# =============================================================================

def test_ini_loader_load_simple():
    """
        Test that IniLoader can load simple INI content.
    """
    content = """
[database]
host = localhost
port = 5432
"""
    loader = IniLoader()
    result = loader.load(content)
    
    if result.get("database.host") != "localhost":
        errmsg = f"Expected database.host='localhost', got {result.get('database.host')}"
        raise AssertionError(errmsg)
    
    if result.get("database.port") != "5432":
        errmsg = f"Expected database.port='5432', got {result.get('database.port')}"
        raise AssertionError(errmsg)
    
    return


def test_ini_loader_load_multiple_sections():
    """
        Test that IniLoader can load multiple sections.
    """
    content = """
[database]
host = localhost

[logging]
level = DEBUG
"""
    loader = IniLoader()
    result = loader.load(content)
    
    if result.get("database.host") != "localhost":
        errmsg = f"Expected database.host='localhost', got {result.get('database.host')}"
        raise AssertionError(errmsg)
    
    if result.get("logging.level") != "DEBUG":
        errmsg = f"Expected logging.level='DEBUG', got {result.get('logging.level')}"
        raise AssertionError(errmsg)
    
    return


def test_ini_loader_dump_simple():
    """
        Test that IniLoader can dump simple configuration.
    """
    data = {
        "database.host": "localhost",
        "database.port": "5432"
    }
    
    loader = IniLoader()
    result = loader.dump(data)
    
    # Parse the result back to verify
    parsed = loader.load(result)
    
    if parsed.get("database.host") != "localhost":
        errmsg = f"Expected database.host='localhost', got {parsed.get('database.host')}"
        raise AssertionError(errmsg)
    
    if parsed.get("database.port") != "5432":
        errmsg = f"Expected database.port='5432', got {parsed.get('database.port')}"
        raise AssertionError(errmsg)
    
    return


# =============================================================================
# Unit Tests for JsonLoader
# =============================================================================

def test_json_loader_load_simple():
    """
        Test that JsonLoader can load simple JSON content.
    """
    content = '{"database": {"host": "localhost", "port": 5432}}'
    
    loader = JsonLoader()
    result = loader.load(content)
    
    if result.get("database.host") != "localhost":
        errmsg = f"Expected database.host='localhost', got {result.get('database.host')}"
        raise AssertionError(errmsg)
    
    if result.get("database.port") != 5432:
        errmsg = f"Expected database.port=5432, got {result.get('database.port')}"
        raise AssertionError(errmsg)
    
    return


def test_json_loader_load_nested():
    """
        Test that JsonLoader can load deeply nested JSON content.
    """
    content = '{"a": {"b": {"c": "deep_value"}}}'
    
    loader = JsonLoader()
    result = loader.load(content)
    
    if result.get("a.b.c") != "deep_value":
        errmsg = f"Expected a.b.c='deep_value', got {result.get('a.b.c')}"
        raise AssertionError(errmsg)
    
    return


def test_json_loader_dump_simple():
    """
        Test that JsonLoader can dump simple configuration.
    """
    data = {
        "database.host": "localhost",
        "database.port": 5432
    }
    
    loader = JsonLoader()
    result = loader.dump(data)
    
    # Parse the result back to verify
    parsed = loader.load(result)
    
    if parsed.get("database.host") != "localhost":
        errmsg = f"Expected database.host='localhost', got {parsed.get('database.host')}"
        raise AssertionError(errmsg)
    
    if parsed.get("database.port") != 5432:
        errmsg = f"Expected database.port=5432, got {parsed.get('database.port')}"
        raise AssertionError(errmsg)
    
    return


def test_json_loader_load_invalid():
    """
        Test that JsonLoader raises error on invalid JSON.
    """
    content = '{"invalid": json}'
    
    loader = JsonLoader()
    
    try:
        loader.load(content)
        errmsg = "Expected ConfigurationError for invalid JSON"
        raise AssertionError(errmsg)
    except ConfigurationError:
        pass  # Expected
    
    return


# =============================================================================
# Unit Tests for YamlLoader (if available)
# =============================================================================

def test_yaml_loader_load_simple():
    """
        Test that YamlLoader can load simple YAML content.
    """
    if not YAML_AVAILABLE:
        return  # Skip if YAML not available
    
    content = """
database:
  host: localhost
  port: 5432
"""
    loader = YamlLoader()
    result = loader.load(content)
    
    if result.get("database.host") != "localhost":
        errmsg = f"Expected database.host='localhost', got {result.get('database.host')}"
        raise AssertionError(errmsg)
    
    if result.get("database.port") != 5432:
        errmsg = f"Expected database.port=5432, got {result.get('database.port')}"
        raise AssertionError(errmsg)
    
    return


def test_yaml_loader_dump_simple():
    """
        Test that YamlLoader can dump simple configuration.
    """
    if not YAML_AVAILABLE:
        return  # Skip if YAML not available
    
    data = {
        "database.host": "localhost",
        "database.port": 5432
    }
    
    loader = YamlLoader()
    result = loader.dump(data)
    
    # Parse the result back to verify
    parsed = loader.load(result)
    
    if parsed.get("database.host") != "localhost":
        errmsg = f"Expected database.host='localhost', got {parsed.get('database.host')}"
        raise AssertionError(errmsg)
    
    if parsed.get("database.port") != 5432:
        errmsg = f"Expected database.port=5432, got {parsed.get('database.port')}"
        raise AssertionError(errmsg)
    
    return


# =============================================================================
# Unit Tests for TomlLoader (if available)
# =============================================================================

def test_toml_loader_load_simple():
    """
        Test that TomlLoader can load simple TOML content.
    """
    if not TOML_AVAILABLE:
        return  # Skip if TOML not available
    
    content = """
[database]
host = "localhost"
port = 5432
"""
    loader = TomlLoader()
    result = loader.load(content)
    
    if result.get("database.host") != "localhost":
        errmsg = f"Expected database.host='localhost', got {result.get('database.host')}"
        raise AssertionError(errmsg)
    
    if result.get("database.port") != 5432:
        errmsg = f"Expected database.port=5432, got {result.get('database.port')}"
        raise AssertionError(errmsg)
    
    return


# =============================================================================
# Unit Tests for FileSource
# =============================================================================

def test_file_source_creation():
    """
        Test that FileSource can be created with paths.
    """
    source = FileSource(paths=[Path("config.json")])
    
    if len(source.paths) != 1:
        errmsg = f"Expected 1 path, got {len(source.paths)}"
        raise AssertionError(errmsg)
    
    if source.source_type != ConfigSourceType.FILE:
        errmsg = f"Expected source_type FILE, got {source.source_type}"
        raise AssertionError(errmsg)
    
    return


def test_file_source_load_json():
    """
        Test that FileSource can load a JSON file.
    """
    # Create a temporary directory and file
    temp_dir = tempfile.mkdtemp()
    
    try:
        config_path = Path(temp_dir) / "config.json"
        config_path.write_text('{"database": {"host": "localhost"}}')
        
        source = FileSource(paths=[config_path])
        result = source.load()
        
        if result.get("database.host") != "localhost":
            errmsg = f"Expected database.host='localhost', got {result.get('database.host')}"
            raise AssertionError(errmsg)
    finally:
        shutil.rmtree(temp_dir)
    
    return


def test_file_source_load_ini():
    """
        Test that FileSource can load an INI file.
    """
    temp_dir = tempfile.mkdtemp()
    
    try:
        config_path = Path(temp_dir) / "config.ini"
        config_path.write_text("[database]\nhost = localhost\n")
        
        source = FileSource(paths=[config_path])
        result = source.load()
        
        if result.get("database.host") != "localhost":
            errmsg = f"Expected database.host='localhost', got {result.get('database.host')}"
            raise AssertionError(errmsg)
    finally:
        shutil.rmtree(temp_dir)
    
    return


def test_file_source_load_missing_optional():
    """
        Test that FileSource returns empty dict for missing optional file.
    """
    source = FileSource(paths=[Path("/nonexistent/config.json")], required=False)
    result = source.load()
    
    if result != {}:
        errmsg = f"Expected empty dict for missing optional file, got {result}"
        raise AssertionError(errmsg)
    
    return


def test_file_source_load_missing_required():
    """
        Test that FileSource raises error for missing required file.
    """
    source = FileSource(paths=[Path("/nonexistent/config.json")], required=True)
    
    try:
        source.load()
        errmsg = "Expected ConfigurationFileNotFoundError for missing required file"
        raise AssertionError(errmsg)
    except ConfigurationFileNotFoundError:
        pass  # Expected
    
    return


def test_file_source_load_multiple_files():
    """
        Test that FileSource merges multiple files with precedence.
    """
    temp_dir = tempfile.mkdtemp()
    
    try:
        # Create two config files
        base_path = Path(temp_dir) / "base.json"
        base_path.write_text('{"database": {"host": "base_host", "port": 5432}}')
        
        override_path = Path(temp_dir) / "override.json"
        override_path.write_text('{"database": {"host": "override_host"}}')
        
        # Load with override taking precedence
        source = FileSource(paths=[base_path, override_path])
        result = source.load()
        
        # Override should win for host
        if result.get("database.host") != "override_host":
            errmsg = f"Expected database.host='override_host', got {result.get('database.host')}"
            raise AssertionError(errmsg)
        
        # Base should provide port
        if result.get("database.port") != 5432:
            errmsg = f"Expected database.port=5432, got {result.get('database.port')}"
            raise AssertionError(errmsg)
    finally:
        shutil.rmtree(temp_dir)
    
    return


def test_file_source_explicit_format():
    """
        Test that FileSource uses explicit format when provided.
    """
    temp_dir = tempfile.mkdtemp()
    
    try:
        # Create a file without extension
        config_path = Path(temp_dir) / "config"
        config_path.write_text('{"database": {"host": "localhost"}}')
        
        # Load with explicit format
        source = FileSource(paths=[config_path], format="json")
        result = source.load()
        
        if result.get("database.host") != "localhost":
            errmsg = f"Expected database.host='localhost', got {result.get('database.host')}"
            raise AssertionError(errmsg)
    finally:
        shutil.rmtree(temp_dir)
    
    return


# =============================================================================
# Property-Based Tests for File Format Round-Trip
# =============================================================================

# Feature: configuration-system, Property 6: File Format Round-Trip
# *For any* valid configuration dictionary, exporting to a file format
# (INI, YAML, JSON, TOML) and then loading from that file SHALL produce
# an equivalent configuration dictionary.
# **Validates: Requirements 2.2, 2.3, 2.4, 2.5**

def test_property_6_file_format_round_trip_json():
    """
        Property 6: File Format Round-Trip (JSON)
        
        For any valid configuration dictionary, exporting to JSON format
        and then loading from that content SHALL produce an equivalent
        configuration dictionary.
        
        **Feature: configuration-system, Property 6: File Format Round-Trip**
        **Validates: Requirements 2.4**
    """
    loader = JsonLoader()
    
    # Run 100 iterations with random data
    for iteration in range(100):
        # Generate random configuration
        original = generate_random_config_dict()
        
        # Dump to JSON
        json_content = loader.dump(original)
        
        # Load back
        loaded = loader.load(json_content)
        
        # Verify all keys and values match
        for key, expected_value in original.items():
            if key not in loaded:
                errmsg = f"Iteration {iteration}: Expected key '{key}' in loaded config"
                raise AssertionError(errmsg)
            
            if loaded[key] != expected_value:
                errmsg = f"Iteration {iteration}: Expected value '{expected_value}' for key '{key}', got '{loaded[key]}'"
                raise AssertionError(errmsg)
        
        # Verify no extra keys
        if len(loaded) != len(original):
            errmsg = f"Iteration {iteration}: Expected {len(original)} keys, got {len(loaded)}"
            raise AssertionError(errmsg)
    
    return


def test_property_6_file_format_round_trip_ini():
    """
        Property 6: File Format Round-Trip (INI)
        
        For any valid configuration dictionary with string values,
        exporting to INI format and then loading from that content
        SHALL produce an equivalent configuration dictionary.
        
        Note: INI format stores all values as strings, so we normalize
        values for comparison.
        
        **Feature: configuration-system, Property 6: File Format Round-Trip**
        **Validates: Requirements 2.2**
    """
    loader = IniLoader()
    
    # Run 100 iterations with random data
    for iteration in range(100):
        # Generate random configuration (INI requires section.key format)
        original = {}
        num_keys = random.randint(1, 5)
        
        for _ in range(num_keys):
            # INI requires at least one dot (section.key)
            key = generate_random_config_key(num_parts=2)
            value = generate_random_simple_value()
            original[key] = value
        
        # Normalize to strings for INI
        original_normalized = normalize_config_values(original)
        
        # Dump to INI
        ini_content = loader.dump(original_normalized)
        
        # Load back
        loaded = loader.load(ini_content)
        
        # Verify all keys and values match (INI lowercases keys)
        for key, expected_value in original_normalized.items():
            lower_key = key.lower()
            if lower_key not in loaded:
                errmsg = f"Iteration {iteration}: Expected key '{lower_key}' in loaded config, got {loaded}"
                raise AssertionError(errmsg)
            
            if loaded[lower_key] != expected_value:
                errmsg = f"Iteration {iteration}: Expected value '{expected_value}' for key '{lower_key}', got '{loaded[lower_key]}'"
                raise AssertionError(errmsg)
    
    return


def test_property_6_file_format_round_trip_yaml():
    """
        Property 6: File Format Round-Trip (YAML)
        
        For any valid configuration dictionary, exporting to YAML format
        and then loading from that content SHALL produce an equivalent
        configuration dictionary.
        
        **Feature: configuration-system, Property 6: File Format Round-Trip**
        **Validates: Requirements 2.3**
    """
    if not YAML_AVAILABLE:
        return  # Skip if YAML not available
    
    loader = YamlLoader()
    
    # Run 100 iterations with random data
    for iteration in range(100):
        # Generate random configuration
        original = generate_random_config_dict()
        
        # Dump to YAML
        yaml_content = loader.dump(original)
        
        # Load back
        loaded = loader.load(yaml_content)
        
        # Verify all keys and values match
        for key, expected_value in original.items():
            if key not in loaded:
                errmsg = f"Iteration {iteration}: Expected key '{key}' in loaded config"
                raise AssertionError(errmsg)
            
            if loaded[key] != expected_value:
                errmsg = f"Iteration {iteration}: Expected value '{expected_value}' for key '{key}', got '{loaded[key]}'"
                raise AssertionError(errmsg)
        
        # Verify no extra keys
        if len(loaded) != len(original):
            errmsg = f"Iteration {iteration}: Expected {len(original)} keys, got {len(loaded)}"
            raise AssertionError(errmsg)
    
    return


def test_property_6_file_format_round_trip_file_source():
    """
        Property 6: File Format Round-Trip (FileSource)
        
        For any valid configuration dictionary, writing to a file and
        loading via FileSource SHALL produce an equivalent configuration.
        
        **Feature: configuration-system, Property 6: File Format Round-Trip**
        **Validates: Requirements 2.2, 2.3, 2.4, 2.5**
    """
    temp_dir = tempfile.mkdtemp()
    
    try:
        # Test JSON format
        json_loader = JsonLoader()
        
        for iteration in range(50):
            # Generate random configuration
            original = generate_random_config_dict()
            
            # Write to file
            config_path = Path(temp_dir) / f"config_{iteration}.json"
            json_content = json_loader.dump(original)
            config_path.write_text(json_content)
            
            # Load via FileSource
            source = FileSource(paths=[config_path])
            loaded = source.load()
            
            # Verify all keys and values match
            for key, expected_value in original.items():
                if key not in loaded:
                    errmsg = f"Iteration {iteration}: Expected key '{key}' in loaded config"
                    raise AssertionError(errmsg)
                
                if loaded[key] != expected_value:
                    errmsg = f"Iteration {iteration}: Expected value '{expected_value}' for key '{key}', got '{loaded[key]}'"
                    raise AssertionError(errmsg)
    finally:
        shutil.rmtree(temp_dir)
    
    return



# =============================================================================
# Unit Tests for Include Directive Processing
# =============================================================================

def test_file_source_include_directive_ini_different_sections():
    """
        Test that FileSource processes include directives in INI files
        when included file has different sections.
    """
    temp_dir = tempfile.mkdtemp()
    
    try:
        # Create included file with different section
        included_path = Path(temp_dir) / "included.ini"
        included_path.write_text("[logging]\nlevel = DEBUG\n")
        
        # Create main file with include directive
        main_path = Path(temp_dir) / "main.ini"
        main_path.write_text(f'%include "{included_path}"\n\n[database]\nhost = localhost\n')
        
        source = FileSource(paths=[main_path])
        result = source.load()
        
        # Should have both values from different sections
        if result.get("database.host") != "localhost":
            errmsg = f"Expected database.host='localhost', got {result.get('database.host')}"
            raise AssertionError(errmsg)
        
        if result.get("logging.level") != "DEBUG":
            errmsg = f"Expected logging.level='DEBUG', got {result.get('logging.level')}"
            raise AssertionError(errmsg)
    finally:
        shutil.rmtree(temp_dir)
    
    return


def test_file_source_include_directive_yaml():
    """
        Test that FileSource processes include directives in YAML files.
    """
    if not YAML_AVAILABLE:
        return  # Skip if YAML not available
    
    temp_dir = tempfile.mkdtemp()
    
    try:
        # Create included file
        included_path = Path(temp_dir) / "included.yaml"
        included_path.write_text("logging:\n  level: DEBUG\n")
        
        # Create main file with include directive (include at top, different section)
        main_path = Path(temp_dir) / "main.yaml"
        main_path.write_text(f'# !include "{included_path}"\n\ndatabase:\n  host: localhost\n')
        
        source = FileSource(paths=[main_path])
        result = source.load()
        
        # Should have host from main file
        if result.get("database.host") != "localhost":
            errmsg = f"Expected database.host='localhost', got {result.get('database.host')}"
            raise AssertionError(errmsg)
        
        # Should have logging from included file
        if result.get("logging.level") != "DEBUG":
            errmsg = f"Expected logging.level='DEBUG', got {result.get('logging.level')}"
            raise AssertionError(errmsg)
    finally:
        shutil.rmtree(temp_dir)
    
    return


def test_file_source_include_directive_relative_path():
    """
        Test that FileSource resolves relative include paths.
    """
    temp_dir = tempfile.mkdtemp()
    
    try:
        # Create subdirectory
        subdir = Path(temp_dir) / "subdir"
        subdir.mkdir()
        
        # Create included file in subdirectory with different section
        included_path = subdir / "included.ini"
        included_path.write_text("[logging]\nlevel = DEBUG\n")
        
        # Create main file with relative include
        main_path = Path(temp_dir) / "main.ini"
        main_path.write_text('%include "subdir/included.ini"\n\n[database]\nhost = localhost\n')
        
        source = FileSource(paths=[main_path])
        result = source.load()
        
        if result.get("logging.level") != "DEBUG":
            errmsg = f"Expected logging.level='DEBUG', got {result.get('logging.level')}"
            raise AssertionError(errmsg)
        
        if result.get("database.host") != "localhost":
            errmsg = f"Expected database.host='localhost', got {result.get('database.host')}"
            raise AssertionError(errmsg)
    finally:
        shutil.rmtree(temp_dir)
    
    return


def test_file_source_include_directive_missing_file():
    """
        Test that FileSource raises error for missing included file.
    """
    temp_dir = tempfile.mkdtemp()
    
    try:
        # Create main file with include to non-existent file
        main_path = Path(temp_dir) / "main.ini"
        main_path.write_text('[database]\nhost = localhost\n\n%include "nonexistent.ini"\n')
        
        source = FileSource(paths=[main_path])
        
        try:
            source.load()
            errmsg = "Expected ConfigurationFileNotFoundError for missing included file"
            raise AssertionError(errmsg)
        except ConfigurationFileNotFoundError as e:
            # Verify the error includes the referencing file
            if e.referenced_from is None:
                errmsg = "Expected referenced_from to be set"
                raise AssertionError(errmsg)
    finally:
        shutil.rmtree(temp_dir)
    
    return


def test_file_source_include_directive_circular():
    """
        Test that FileSource detects circular includes.
    """
    temp_dir = tempfile.mkdtemp()
    
    try:
        # Create two files that include each other
        file_a = Path(temp_dir) / "a.ini"
        file_b = Path(temp_dir) / "b.ini"
        
        file_a.write_text(f'[section_a]\nkey = value_a\n\n%include "{file_b}"\n')
        file_b.write_text(f'[section_b]\nkey = value_b\n\n%include "{file_a}"\n')
        
        source = FileSource(paths=[file_a])
        
        try:
            source.load()
            errmsg = "Expected ConfigurationError for circular include"
            raise AssertionError(errmsg)
        except ConfigurationError as e:
            if "Circular" not in str(e):
                errmsg = f"Expected circular include error, got: {e}"
                raise AssertionError(errmsg)
    finally:
        shutil.rmtree(temp_dir)
    
    return


def test_file_source_include_disabled():
    """
        Test that FileSource can disable include processing.
    """
    temp_dir = tempfile.mkdtemp()
    
    try:
        # Create main file with include directive (as a comment-like line that won't break INI)
        main_path = Path(temp_dir) / "main.json"
        main_path.write_text('{"database": {"host": "localhost"}}')
        
        # With process_includes=False, the include directive should be ignored
        source = FileSource(paths=[main_path], process_includes=False)
        result = source.load()
        
        # Should load without error
        if result.get("database.host") != "localhost":
            errmsg = f"Expected database.host='localhost', got {result.get('database.host')}"
            raise AssertionError(errmsg)
    finally:
        shutil.rmtree(temp_dir)
    
    return



# =============================================================================
# Property-Based Tests for Include Directive Processing
# =============================================================================

# Feature: configuration-system, Property 20: Include Directive Processing
# *For any* configuration file with include directives, the included files
# SHALL be loaded and merged into the configuration.
# **Validates: Requirements 5.7**

def generate_ini_safe_value() -> Any:
    """
        Generate a random value safe for INI format (string or int only).
        
        :returns: A random string or int value.
    """
    value_type = random.choice(["string", "int"])
    
    if value_type == "string":
        length = random.randint(1, 20)
        chars = string.ascii_letters + string.digits
        return ''.join(random.choice(chars) for _ in range(length))
    else:
        return random.randint(0, 10000)


def test_property_20_include_directive_processing():
    """
        Property 20: Include Directive Processing
        
        For any configuration file with include directives, the included
        files SHALL be loaded and merged into the configuration.
        
        **Feature: configuration-system, Property 20: Include Directive Processing**
        **Validates: Requirements 5.7**
    """
    temp_dir = tempfile.mkdtemp()
    
    try:
        # Run 100 iterations with random data
        for iteration in range(100):
            # Generate random configuration for included file
            included_config = {}
            num_included_keys = random.randint(1, 3)
            for i in range(num_included_keys):
                section = f"included_section_{i}"
                key = generate_random_key_part()
                value = generate_ini_safe_value()
                included_config[f"{section}.{key}"] = value
            
            # Generate random configuration for main file
            main_config = {}
            num_main_keys = random.randint(1, 3)
            for i in range(num_main_keys):
                section = f"main_section_{i}"
                key = generate_random_key_part()
                value = generate_ini_safe_value()
                main_config[f"{section}.{key}"] = value
            
            # Create included INI file
            included_path = Path(temp_dir) / f"included_{iteration}.ini"
            included_content = ""
            sections_written = set()
            for full_key, value in included_config.items():
                section, key = full_key.split(".", 1)
                if section not in sections_written:
                    included_content += f"[{section}]\n"
                    sections_written.add(section)
                included_content += f"{key} = {value}\n"
            included_path.write_text(included_content)
            
            # Create main INI file with include directive
            main_path = Path(temp_dir) / f"main_{iteration}.ini"
            main_content = f'%include "{included_path}"\n\n'
            sections_written = set()
            for full_key, value in main_config.items():
                section, key = full_key.split(".", 1)
                if section not in sections_written:
                    main_content += f"[{section}]\n"
                    sections_written.add(section)
                main_content += f"{key} = {value}\n"
            main_path.write_text(main_content)
            
            # Load via FileSource
            source = FileSource(paths=[main_path])
            result = source.load()
            
            # Verify all included keys are present (INI lowercases keys)
            for full_key, expected_value in included_config.items():
                lower_key = full_key.lower()
                if lower_key not in result:
                    errmsg = f"Iteration {iteration}: Expected included key '{lower_key}' in result"
                    raise AssertionError(errmsg)
                
                # INI stores everything as strings
                expected_str = str(expected_value)
                if result[lower_key] != expected_str:
                    errmsg = f"Iteration {iteration}: Expected value '{expected_str}' for included key '{lower_key}', got '{result[lower_key]}'"
                    raise AssertionError(errmsg)
            
            # Verify all main keys are present
            for full_key, expected_value in main_config.items():
                lower_key = full_key.lower()
                if lower_key not in result:
                    errmsg = f"Iteration {iteration}: Expected main key '{lower_key}' in result"
                    raise AssertionError(errmsg)
                
                expected_str = str(expected_value)
                if result[lower_key] != expected_str:
                    errmsg = f"Iteration {iteration}: Expected value '{expected_str}' for main key '{lower_key}', got '{result[lower_key]}'"
                    raise AssertionError(errmsg)
    finally:
        shutil.rmtree(temp_dir)
    
    return


def test_property_20_include_directive_nested():
    """
        Property 20 (Extended): Nested Include Directive Processing
        
        For any configuration file with nested include directives (A includes B,
        B includes C), all included files SHALL be loaded and merged.
        
        **Feature: configuration-system, Property 20: Include Directive Processing**
        **Validates: Requirements 5.7**
    """
    temp_dir = tempfile.mkdtemp()
    
    try:
        # Run 50 iterations with random data
        for iteration in range(50):
            # Generate random configuration for each level (using INI-safe values)
            level_c_config = {f"level_c.key_{iteration}": generate_ini_safe_value()}
            level_b_config = {f"level_b.key_{iteration}": generate_ini_safe_value()}
            level_a_config = {f"level_a.key_{iteration}": generate_ini_safe_value()}
            
            # Create level C file (no includes)
            level_c_path = Path(temp_dir) / f"level_c_{iteration}.ini"
            level_c_content = "[level_c]\n"
            for full_key, value in level_c_config.items():
                _, key = full_key.split(".", 1)
                level_c_content += f"{key} = {value}\n"
            level_c_path.write_text(level_c_content)
            
            # Create level B file (includes C)
            level_b_path = Path(temp_dir) / f"level_b_{iteration}.ini"
            level_b_content = f'%include "{level_c_path}"\n\n[level_b]\n'
            for full_key, value in level_b_config.items():
                _, key = full_key.split(".", 1)
                level_b_content += f"{key} = {value}\n"
            level_b_path.write_text(level_b_content)
            
            # Create level A file (includes B)
            level_a_path = Path(temp_dir) / f"level_a_{iteration}.ini"
            level_a_content = f'%include "{level_b_path}"\n\n[level_a]\n'
            for full_key, value in level_a_config.items():
                _, key = full_key.split(".", 1)
                level_a_content += f"{key} = {value}\n"
            level_a_path.write_text(level_a_content)
            
            # Load via FileSource
            source = FileSource(paths=[level_a_path])
            result = source.load()
            
            # Verify all levels are present
            all_configs = {**level_c_config, **level_b_config, **level_a_config}
            for full_key, expected_value in all_configs.items():
                lower_key = full_key.lower()
                if lower_key not in result:
                    errmsg = f"Iteration {iteration}: Expected key '{lower_key}' in result"
                    raise AssertionError(errmsg)
                
                expected_str = str(expected_value)
                if result[lower_key] != expected_str:
                    errmsg = f"Iteration {iteration}: Expected value '{expected_str}' for key '{lower_key}', got '{result[lower_key]}'"
                    raise AssertionError(errmsg)
    finally:
        shutil.rmtree(temp_dir)
    
    return



# =============================================================================
# Property-Based Tests for Missing File Error
# =============================================================================

# Feature: configuration-system, Property 21: Missing File Error
# *For any* referenced configuration file that does not exist,
# ConfigurationFileNotFoundError SHALL be raised.
# **Validates: Requirements 5.8**

def test_property_21_missing_file_error():
    """
        Property 21: Missing File Error
        
        For any referenced configuration file that does not exist,
        ConfigurationFileNotFoundError SHALL be raised.
        
        **Feature: configuration-system, Property 21: Missing File Error**
        **Validates: Requirements 5.8**
    """
    temp_dir = tempfile.mkdtemp()
    
    try:
        # Run 100 iterations with random file paths
        for iteration in range(100):
            # Generate a random non-existent file path
            random_filename = ''.join(random.choice(string.ascii_lowercase) for _ in range(10))
            random_ext = random.choice([".json", ".yaml", ".ini", ".toml"])
            nonexistent_path = Path(temp_dir) / f"{random_filename}_{iteration}{random_ext}"
            
            # Ensure the file doesn't exist
            if nonexistent_path.exists():
                nonexistent_path.unlink()
            
            # Create FileSource with required=True
            source = FileSource(paths=[nonexistent_path], required=True)
            
            # Attempt to load should raise ConfigurationFileNotFoundError
            try:
                source.load()
                errmsg = f"Iteration {iteration}: Expected ConfigurationFileNotFoundError for missing file {nonexistent_path}"
                raise AssertionError(errmsg)
            except ConfigurationFileNotFoundError as e:
                # Verify the error contains the correct path
                if e.path != nonexistent_path:
                    errmsg = f"Iteration {iteration}: Expected path '{nonexistent_path}' in error, got '{e.path}'"
                    raise AssertionError(errmsg)
    finally:
        shutil.rmtree(temp_dir)
    
    return


def test_property_21_missing_included_file_error():
    """
        Property 21 (Extended): Missing Included File Error
        
        For any include directive referencing a non-existent file,
        ConfigurationFileNotFoundError SHALL be raised with the
        referenced_from path set.
        
        **Feature: configuration-system, Property 21: Missing File Error**
        **Validates: Requirements 5.8**
    """
    temp_dir = tempfile.mkdtemp()
    
    try:
        # Run 100 iterations with random file paths
        for iteration in range(100):
            # Generate a random non-existent file path for the include
            random_filename = ''.join(random.choice(string.ascii_lowercase) for _ in range(10))
            nonexistent_include = f"{random_filename}_{iteration}.ini"
            
            # Create main file with include to non-existent file
            main_path = Path(temp_dir) / f"main_{iteration}.ini"
            main_path.write_text(f'[database]\nhost = localhost\n\n%include "{nonexistent_include}"\n')
            
            # Create FileSource
            source = FileSource(paths=[main_path])
            
            # Attempt to load should raise ConfigurationFileNotFoundError
            try:
                source.load()
                errmsg = f"Iteration {iteration}: Expected ConfigurationFileNotFoundError for missing included file"
                raise AssertionError(errmsg)
            except ConfigurationFileNotFoundError as e:
                # Verify the error contains the referenced_from path
                if e.referenced_from is None:
                    errmsg = f"Iteration {iteration}: Expected referenced_from to be set"
                    raise AssertionError(errmsg)
                
                # Verify referenced_from points to the main file
                if e.referenced_from != main_path:
                    errmsg = f"Iteration {iteration}: Expected referenced_from '{main_path}', got '{e.referenced_from}'"
                    raise AssertionError(errmsg)
    finally:
        shutil.rmtree(temp_dir)
    
    return


def test_property_21_optional_missing_file_no_error():
    """
        Property 21 (Extended): Optional Missing File No Error
        
        For any optional configuration file that does not exist,
        no error SHALL be raised and an empty configuration SHALL be returned.
        
        **Feature: configuration-system, Property 21: Missing File Error**
        **Validates: Requirements 5.8**
    """
    temp_dir = tempfile.mkdtemp()
    
    try:
        # Run 100 iterations with random file paths
        for iteration in range(100):
            # Generate a random non-existent file path
            random_filename = ''.join(random.choice(string.ascii_lowercase) for _ in range(10))
            random_ext = random.choice([".json", ".yaml", ".ini", ".toml"])
            nonexistent_path = Path(temp_dir) / f"{random_filename}_{iteration}{random_ext}"
            
            # Ensure the file doesn't exist
            if nonexistent_path.exists():
                nonexistent_path.unlink()
            
            # Create FileSource with required=False (default)
            source = FileSource(paths=[nonexistent_path], required=False)
            
            # Load should succeed and return empty dict
            result = source.load()
            
            if result != {}:
                errmsg = f"Iteration {iteration}: Expected empty dict for optional missing file, got {result}"
                raise AssertionError(errmsg)
    finally:
        shutil.rmtree(temp_dir)
    
    return


# =============================================================================
# SecretsProvider Tests
# =============================================================================

from ccai.webworks.configuration import SecretsProvider, SecretValue


# =============================================================================
# Unit Tests for SecretsProvider
# =============================================================================

def test_secrets_provider_creation_defaults():
    """
        Test that SecretsProvider can be created with default parameters.
    """
    provider = SecretsProvider()
    
    if provider.env_prefix != "SECRET_":
        errmsg = f"Expected env_prefix 'SECRET_', got {provider.env_prefix}"
        raise AssertionError(errmsg)
    
    if provider.secrets_file is not None:
        errmsg = f"Expected secrets_file None, got {provider.secrets_file}"
        raise AssertionError(errmsg)
    
    if provider.source_type != ConfigSourceType.SECRETS:
        errmsg = f"Expected source_type SECRETS, got {provider.source_type}"
        raise AssertionError(errmsg)
    
    return


def test_secrets_provider_creation_custom():
    """
        Test that SecretsProvider can be created with custom parameters.
    """
    temp_dir = tempfile.mkdtemp()
    
    try:
        secrets_path = Path(temp_dir) / "secrets.enc"
        encryption_key = b"test-encryption-key-32-bytes!!"
        
        def audit_log(key: str):
            pass
        
        provider = SecretsProvider(
            env_prefix="MYSECRET_",
            secrets_file=secrets_path,
            encryption_key=encryption_key,
            audit_logger=audit_log
        )
        
        if provider.env_prefix != "MYSECRET_":
            errmsg = f"Expected env_prefix 'MYSECRET_', got {provider.env_prefix}"
            raise AssertionError(errmsg)
        
        if provider.secrets_file != secrets_path:
            errmsg = f"Expected secrets_file '{secrets_path}', got {provider.secrets_file}"
            raise AssertionError(errmsg)
    finally:
        shutil.rmtree(temp_dir)
    
    return


def test_secrets_provider_load_from_environment():
    """
        Test that SecretsProvider loads secrets from environment variables.
    """
    env_vars = {
        "TEST_SECRET_DATABASE_PASSWORD": "db_secret_123",
        "TEST_SECRET_API_KEY": "api_key_456"
    }
    
    try:
        set_test_env_vars(env_vars)
        
        provider = SecretsProvider(env_prefix="TEST_SECRET_")
        result = provider.load()
        
        if "database.password" not in result:
            errmsg = f"Expected 'database.password' in result, got {result.keys()}"
            raise AssertionError(errmsg)
        
        if "api.key" not in result:
            errmsg = f"Expected 'api.key' in result, got {result.keys()}"
            raise AssertionError(errmsg)
        
        # Verify values are SecretValue instances
        if not isinstance(result["database.password"], SecretValue):
            errmsg = f"Expected SecretValue, got {type(result['database.password'])}"
            raise AssertionError(errmsg)
        
        # Verify actual values
        if result["database.password"].get_secret_value() != "db_secret_123":
            errmsg = f"Expected 'db_secret_123', got {result['database.password'].get_secret_value()}"
            raise AssertionError(errmsg)
        
        if result["api.key"].get_secret_value() != "api_key_456":
            errmsg = f"Expected 'api_key_456', got {result['api.key'].get_secret_value()}"
            raise AssertionError(errmsg)
    finally:
        clear_test_env_vars(env_vars)
    
    return


def test_secrets_provider_load_empty():
    """
        Test that SecretsProvider returns empty dict when no secrets found.
    """
    provider = SecretsProvider(env_prefix="UNIQUE_SECRET_PREFIX_12345_")
    result = provider.load()
    
    if result != {}:
        errmsg = f"Expected empty dict, got {result}"
        raise AssertionError(errmsg)
    
    return


def test_secrets_provider_get_secret():
    """
        Test that SecretsProvider.get_secret() returns correct SecretValue.
    """
    env_vars = {"TEST_GET_SECRET_MY_KEY": "my_secret_value"}
    
    try:
        set_test_env_vars(env_vars)
        
        provider = SecretsProvider(env_prefix="TEST_GET_SECRET_")
        
        # get_secret should trigger load if not loaded
        secret = provider.get_secret("my.key")
        
        if secret is None:
            errmsg = "Expected SecretValue, got None"
            raise AssertionError(errmsg)
        
        if secret.get_secret_value() != "my_secret_value":
            errmsg = f"Expected 'my_secret_value', got {secret.get_secret_value()}"
            raise AssertionError(errmsg)
        
        # Non-existent key should return None
        missing = provider.get_secret("nonexistent.key")
        if missing is not None:
            errmsg = f"Expected None for missing key, got {missing}"
            raise AssertionError(errmsg)
    finally:
        clear_test_env_vars(env_vars)
    
    return


def test_secrets_provider_reload():
    """
        Test that SecretsProvider.reload() reloads secrets.
    """
    env_vars = {"TEST_RELOAD_SECRET_KEY": "initial_value"}
    
    try:
        set_test_env_vars(env_vars)
        
        provider = SecretsProvider(env_prefix="TEST_RELOAD_SECRET_")
        result1 = provider.load()
        
        if result1["key"].get_secret_value() != "initial_value":
            errmsg = f"Expected 'initial_value', got {result1['key'].get_secret_value()}"
            raise AssertionError(errmsg)
        
        # Change the environment variable
        os.environ["TEST_RELOAD_SECRET_KEY"] = "updated_value"
        
        # Reload
        result2 = provider.reload()
        
        if result2["key"].get_secret_value() != "updated_value":
            errmsg = f"Expected 'updated_value', got {result2['key'].get_secret_value()}"
            raise AssertionError(errmsg)
    finally:
        clear_test_env_vars(env_vars)
    
    return


# =============================================================================
# Property-Based Tests for SecretsProvider
# =============================================================================

# Feature: configuration-system, Property 13: Secret Encryption Round-Trip
# *For any* secret value, encrypting and writing to a secrets file, then
# loading and decrypting SHALL produce the original secret value.
# **Validates: Requirements 4.1**

def test_property_13_secret_encryption_round_trip():
    """
        Property 13: Secret Encryption Round-Trip
        
        For any secret value, encrypting and writing to a secrets file,
        then loading and decrypting SHALL produce the original secret value.
        
        **Feature: configuration-system, Property 13: Secret Encryption Round-Trip**
        **Validates: Requirements 4.1**
    """
    temp_dir = tempfile.mkdtemp()
    
    try:
        # Run 100 iterations with random data
        for iteration in range(100):
            # Generate random encryption key (32 bytes for AES-256)
            encryption_key = os.urandom(32)
            
            # Generate random secrets
            num_secrets = random.randint(1, 5)
            original_secrets: Dict[str, str] = {}
            
            for _ in range(num_secrets):
                key = generate_random_config_key()
                value = generate_random_value()
                original_secrets[key] = value
            
            # Create secrets file path
            secrets_path = Path(temp_dir) / f"secrets_{iteration}.enc"
            
            # Create provider and encrypt secrets
            provider = SecretsProvider(
                secrets_file=secrets_path,
                encryption_key=encryption_key
            )
            
            # Encrypt and write
            provider.write_encrypted_secrets(original_secrets)
            
            # Verify file was created
            if not secrets_path.exists():
                errmsg = f"Iteration {iteration}: Secrets file was not created"
                raise AssertionError(errmsg)
            
            # Create new provider to load and decrypt
            provider2 = SecretsProvider(
                secrets_file=secrets_path,
                encryption_key=encryption_key
            )
            
            # Load secrets
            loaded_secrets = provider2.load()
            
            # Verify all original secrets are present with correct values
            for key, expected_value in original_secrets.items():
                if key not in loaded_secrets:
                    errmsg = f"Iteration {iteration}: Expected key '{key}' in loaded secrets"
                    raise AssertionError(errmsg)
                
                actual_value = loaded_secrets[key].get_secret_value()
                if actual_value != expected_value:
                    errmsg = f"Iteration {iteration}: Expected value '{expected_value}' for key '{key}', got '{actual_value}'"
                    raise AssertionError(errmsg)
            
            # Verify no extra keys
            if len(loaded_secrets) != len(original_secrets):
                errmsg = f"Iteration {iteration}: Expected {len(original_secrets)} secrets, got {len(loaded_secrets)}"
                raise AssertionError(errmsg)
            
            # Clean up for next iteration
            secrets_path.unlink()
    finally:
        shutil.rmtree(temp_dir)
    
    return


def test_property_13_encryption_with_different_keys():
    """
        Property 13 (Extended): Encryption with Different Keys
        
        For any secret encrypted with one key, attempting to decrypt with
        a different key SHALL fail.
        
        **Feature: configuration-system, Property 13: Secret Encryption Round-Trip**
        **Validates: Requirements 4.1**
    """
    temp_dir = tempfile.mkdtemp()
    
    try:
        # Run 50 iterations
        for iteration in range(50):
            # Generate two different encryption keys
            key1 = os.urandom(32)
            key2 = os.urandom(32)
            
            # Ensure keys are different
            while key1 == key2:
                key2 = os.urandom(32)
            
            # Generate random secrets
            original_secrets = {
                generate_random_config_key(): generate_random_value()
                for _ in range(random.randint(1, 3))
            }
            
            secrets_path = Path(temp_dir) / f"secrets_diff_key_{iteration}.enc"
            
            # Encrypt with key1
            provider1 = SecretsProvider(
                secrets_file=secrets_path,
                encryption_key=key1
            )
            provider1.write_encrypted_secrets(original_secrets)
            
            # Try to decrypt with key2 - should fail
            provider2 = SecretsProvider(
                secrets_file=secrets_path,
                encryption_key=key2
            )
            
            try:
                provider2.load()
                errmsg = f"Iteration {iteration}: Expected decryption to fail with wrong key"
                raise AssertionError(errmsg)
            except ConfigurationError:
                pass  # Expected - decryption should fail with wrong key
            
            # Clean up
            secrets_path.unlink()
    finally:
        shutil.rmtree(temp_dir)
    
    return



# Feature: configuration-system, Property 14: Secret Masking
# *For any* configuration key marked as sensitive, the value SHALL be masked
# in string representations, logs, and error messages.
# **Validates: Requirements 4.4, 4.5**

def test_property_14_secret_masking():
    """
        Property 14: Secret Masking
        
        For any configuration key marked as sensitive, the value SHALL be
        masked in string representations, logs, and error messages.
        
        **Feature: configuration-system, Property 14: Secret Masking**
        **Validates: Requirements 4.4, 4.5**
    """
    # Run 100 iterations with random data
    for iteration in range(100):
        # Generate random secret key and value
        # Use longer values to avoid false positives from short values appearing in keys
        key = generate_random_config_key()
        value = ''.join(random.choice(string.ascii_letters + string.digits) for _ in range(20, 50))
        
        # Create SecretValue
        secret = SecretValue(value=value, key=key)
        
        # Test __str__ does not expose value
        str_repr = str(secret)
        if value in str_repr:
            errmsg = f"Iteration {iteration}: Secret value exposed in __str__"
            raise AssertionError(errmsg)
        
        if str_repr != "***MASKED***":
            errmsg = f"Iteration {iteration}: Expected '***MASKED***' in __str__, got: {str_repr}"
            raise AssertionError(errmsg)
        
        # Test __repr__ does not expose value
        repr_str = repr(secret)
        if value in repr_str:
            errmsg = f"Iteration {iteration}: Secret value exposed in __repr__"
            raise AssertionError(errmsg)
        
        if "***MASKED***" not in repr_str:
            errmsg = f"Iteration {iteration}: Expected '***MASKED***' in __repr__, got: {repr_str}"
            raise AssertionError(errmsg)
        
        # Test that key is visible in repr (for debugging)
        if key not in repr_str:
            errmsg = f"Iteration {iteration}: Expected key '{key}' in __repr__, got: {repr_str}"
            raise AssertionError(errmsg)
        
        # Test get_secret_value() returns actual value
        actual = secret.get_secret_value()
        if actual != value:
            errmsg = f"Iteration {iteration}: Expected value from get_secret_value() to match"
            raise AssertionError(errmsg)
    
    return


def test_property_14_secret_masking_in_collections():
    """
        Property 14 (Extended): Secret Masking in Collections
        
        For any SecretValue in a collection (list, dict), converting the
        collection to string SHALL NOT expose the secret value.
        
        **Feature: configuration-system, Property 14: Secret Masking**
        **Validates: Requirements 4.4, 4.5**
    """
    # Run 100 iterations with random data
    for iteration in range(100):
        # Generate random secrets with longer values to avoid false positives
        num_secrets = random.randint(1, 5)
        secrets_dict: Dict[str, SecretValue] = {}
        secrets_list = []
        
        for _ in range(num_secrets):
            key = generate_random_config_key()
            # Use longer values to avoid false positives from short values appearing in keys
            value = ''.join(random.choice(string.ascii_letters + string.digits) for _ in range(20, 50))
            secret = SecretValue(value=value, key=key)
            secrets_dict[key] = secret
            secrets_list.append(secret)
        
        # Convert dict to string
        dict_str = str(secrets_dict)
        
        # Verify no secret values are exposed
        for key, secret in secrets_dict.items():
            actual_value = secret.get_secret_value()
            if actual_value in dict_str:
                errmsg = f"Iteration {iteration}: Secret value exposed in dict string"
                raise AssertionError(errmsg)
        
        # Convert list to string
        list_str = str(secrets_list)
        
        # Verify no secret values are exposed
        for secret in secrets_list:
            actual_value = secret.get_secret_value()
            if actual_value in list_str:
                errmsg = f"Iteration {iteration}: Secret value exposed in list string"
                raise AssertionError(errmsg)
    
    return


def test_property_14_secrets_provider_masking():
    """
        Property 14 (Extended): SecretsProvider Masking
        
        For any secrets loaded via SecretsProvider, the values SHALL be
        wrapped in SecretValue and masked in string representations.
        
        **Feature: configuration-system, Property 14: Secret Masking**
        **Validates: Requirements 4.4, 4.5**
    """
    # Run 100 iterations with random data
    for iteration in range(100):
        # Generate unique prefix for this iteration
        prefix = f"PROP14_ITER{iteration}_"
        
        # Generate random secrets
        num_secrets = random.randint(1, 3)
        env_vars: Dict[str, str] = {}
        expected_values: Dict[str, str] = {}
        
        for i in range(num_secrets):
            key = generate_random_config_key()
            value = generate_random_value()
            env_name = prefix + key.replace(".", "_").upper()
            env_vars[env_name] = value
            expected_values[key] = value
        
        try:
            set_test_env_vars(env_vars)
            
            provider = SecretsProvider(env_prefix=prefix)
            result = provider.load()
            
            # Verify all values are SecretValue instances
            for key, secret in result.items():
                if not isinstance(secret, SecretValue):
                    errmsg = f"Iteration {iteration}: Expected SecretValue for key '{key}', got {type(secret)}"
                    raise AssertionError(errmsg)
                
                # Verify masking
                str_repr = str(secret)
                actual_value = secret.get_secret_value()
                
                # Assert the representation *is* the mask rather than that it
                # merely lacks the value. A containment check false-positives
                # on short secrets: generate_random_value() can return a
                # single character, and "M", "A", "S", "K", "E" and "D" all
                # appear in "***MASKED***", so a correctly masked secret
                # looked leaked roughly one run in ten.
                if str_repr != SecretValue.MASKED_VALUE:
                    errmsg = (f"Iteration {iteration}: Expected "
                              f"'{SecretValue.MASKED_VALUE}' for key '{key}', "
                              f"got: {str_repr}")
                    raise AssertionError(errmsg)
                
                # Verify actual value is correct
                if actual_value != expected_values[key]:
                    errmsg = f"Iteration {iteration}: Expected '{expected_values[key]}' for key '{key}', got '{actual_value}'"
                    raise AssertionError(errmsg)
        finally:
            clear_test_env_vars(env_vars)
    
    return



# Feature: configuration-system, Property 16: Secret Audit Logging
# *For any* access to a sensitive value when audit logging is enabled,
# an audit log entry SHALL be created recording the access.
# **Validates: Requirements 4.9**

def test_property_16_secret_audit_logging():
    """
        Property 16: Secret Audit Logging
        
        For any access to a sensitive value when audit logging is enabled,
        an audit log entry SHALL be created recording the access.
        
        **Feature: configuration-system, Property 16: Secret Audit Logging**
        **Validates: Requirements 4.9**
    """
    # Run 100 iterations with random data
    for iteration in range(100):
        # Create audit log collector
        audit_log = []
        
        def audit_logger(key: str):
            audit_log.append(key)
        
        # Generate random key and value
        key = generate_random_config_key()
        value = generate_random_value()
        
        # Create SecretValue with audit logger
        secret = SecretValue(value=value, key=key, audit_logger=audit_logger)
        
        # Access the secret a random number of times
        num_accesses = random.randint(1, 10)
        
        for _ in range(num_accesses):
            secret.get_secret_value()
        
        # Verify audit log has correct number of entries
        if len(audit_log) != num_accesses:
            errmsg = f"Iteration {iteration}: Expected {num_accesses} audit log entries, got {len(audit_log)}"
            raise AssertionError(errmsg)
        
        # Verify all entries have the correct key
        for entry in audit_log:
            if entry != key:
                errmsg = f"Iteration {iteration}: Expected key '{key}' in audit log, got '{entry}'"
                raise AssertionError(errmsg)
    
    return


def test_property_16_audit_logging_with_secrets_provider():
    """
        Property 16 (Extended): Audit Logging with SecretsProvider
        
        For any secrets loaded via SecretsProvider with audit logging enabled,
        accessing secret values SHALL create audit log entries.
        
        **Feature: configuration-system, Property 16: Secret Audit Logging**
        **Validates: Requirements 4.9**
    """
    # Run 100 iterations with random data
    for iteration in range(100):
        # Create audit log collector
        audit_log = []
        
        def audit_logger(key: str):
            audit_log.append(key)
        
        # Generate unique prefix for this iteration
        prefix = f"PROP16_ITER{iteration}_"
        
        # Generate random secrets
        num_secrets = random.randint(1, 3)
        env_vars: Dict[str, str] = {}
        expected_keys = []
        
        for i in range(num_secrets):
            key = generate_random_config_key()
            value = generate_random_value()
            env_name = prefix + key.replace(".", "_").upper()
            env_vars[env_name] = value
            expected_keys.append(key)
        
        try:
            set_test_env_vars(env_vars)
            
            provider = SecretsProvider(env_prefix=prefix, audit_logger=audit_logger)
            result = provider.load()
            
            # Access each secret
            for key in expected_keys:
                result[key].get_secret_value()
            
            # Verify audit log has entries for all accessed secrets
            if len(audit_log) != len(expected_keys):
                errmsg = f"Iteration {iteration}: Expected {len(expected_keys)} audit log entries, got {len(audit_log)}"
                raise AssertionError(errmsg)
            
            # Verify all expected keys are in audit log
            for key in expected_keys:
                if key not in audit_log:
                    errmsg = f"Iteration {iteration}: Expected key '{key}' in audit log"
                    raise AssertionError(errmsg)
        finally:
            clear_test_env_vars(env_vars)
    
    return


def test_property_16_no_audit_logging_without_logger():
    """
        Property 16 (Extended): No Audit Logging Without Logger
        
        For any SecretValue created without an audit logger, accessing
        the secret value SHALL NOT cause any errors.
        
        **Feature: configuration-system, Property 16: Secret Audit Logging**
        **Validates: Requirements 4.9**
    """
    # Run 100 iterations with random data
    for iteration in range(100):
        # Generate random key and value
        key = generate_random_config_key()
        value = generate_random_value()
        
        # Create SecretValue WITHOUT audit logger
        secret = SecretValue(value=value, key=key)
        
        # Access the secret - should not raise any errors
        actual = secret.get_secret_value()
        
        if actual != value:
            errmsg = f"Iteration {iteration}: Expected '{value}', got '{actual}'"
            raise AssertionError(errmsg)
    
    return


# =============================================================================
# Tests for ConfigFileDiscovery
# =============================================================================

from ccai.webworks.configuration import (
    ConfigFileDiscovery,
    DEFAULT_SEARCH_DIRECTORIES,
    DEFAULT_FILE_PATTERNS,
)


def test_config_file_discovery_creation_defaults():
    """
        Test that ConfigFileDiscovery can be created with default parameters.
    """
    discovery = ConfigFileDiscovery()
    
    if discovery.appname != "app":
        errmsg = f"Expected appname 'app', got {discovery.appname}"
        raise AssertionError(errmsg)
    
    if discovery.search_directories != DEFAULT_SEARCH_DIRECTORIES:
        errmsg = f"Expected default search directories, got {discovery.search_directories}"
        raise AssertionError(errmsg)
    
    if discovery.file_patterns != DEFAULT_FILE_PATTERNS:
        errmsg = f"Expected default file patterns, got {discovery.file_patterns}"
        raise AssertionError(errmsg)
    
    if discovery.environment is not None:
        errmsg = f"Expected environment None, got {discovery.environment}"
        raise AssertionError(errmsg)
    
    return


def test_config_file_discovery_creation_custom():
    """
        Test that ConfigFileDiscovery can be created with custom parameters.
    """
    discovery = ConfigFileDiscovery(
        appname="myapp",
        search_directories=["./custom", "/etc/custom"],
        file_patterns=["*.yaml", "*.json"],
        environment="production",
        profile="web"
    )
    
    if discovery.appname != "myapp":
        errmsg = f"Expected appname 'myapp', got {discovery.appname}"
        raise AssertionError(errmsg)
    
    if discovery.search_directories != ["./custom", "/etc/custom"]:
        errmsg = f"Expected custom search directories, got {discovery.search_directories}"
        raise AssertionError(errmsg)
    
    if discovery.file_patterns != ["*.yaml", "*.json"]:
        errmsg = f"Expected custom file patterns, got {discovery.file_patterns}"
        raise AssertionError(errmsg)
    
    if discovery.environment != "production":
        errmsg = f"Expected environment 'production', got {discovery.environment}"
        raise AssertionError(errmsg)
    
    if discovery.profile != "web":
        errmsg = f"Expected profile 'web', got {discovery.profile}"
        raise AssertionError(errmsg)
    
    return


def test_config_file_discovery_discover_empty_directory():
    """
        Test that ConfigFileDiscovery returns empty list for non-existent directories.
    """
    discovery = ConfigFileDiscovery(
        appname="testapp",
        search_directories=["/nonexistent/directory/12345"]
    )
    
    files = discovery.discover()
    
    if files != []:
        errmsg = f"Expected empty list, got {files}"
        raise AssertionError(errmsg)
    
    return


def test_config_file_discovery_discover_with_files():
    """
        Test that ConfigFileDiscovery discovers files matching patterns.
    """
    # Create a temporary directory with config files
    temp_dir = tempfile.mkdtemp()
    
    try:
        # Create some config files
        settings_yaml = Path(temp_dir) / "settings.yaml"
        settings_yaml.write_text("key: value")
        
        config_json = Path(temp_dir) / "config.json"
        config_json.write_text('{"key": "value"}')
        
        # Create a non-matching file
        readme = Path(temp_dir) / "README.md"
        readme.write_text("# Readme")
        
        discovery = ConfigFileDiscovery(
            appname="testapp",
            search_directories=[temp_dir]
        )
        
        files = discovery.discover()
        
        # Should find settings.yaml and config.json
        filenames = [f.name for f in files]
        
        if "settings.yaml" not in filenames:
            errmsg = f"Expected 'settings.yaml' in discovered files, got {filenames}"
            raise AssertionError(errmsg)
        
        if "config.json" not in filenames:
            errmsg = f"Expected 'config.json' in discovered files, got {filenames}"
            raise AssertionError(errmsg)
        
        # Should NOT find README.md
        if "README.md" in filenames:
            errmsg = f"Did not expect 'README.md' in discovered files, got {filenames}"
            raise AssertionError(errmsg)
    
    finally:
        shutil.rmtree(temp_dir)
    
    return


def test_config_file_discovery_appname_pattern():
    """
        Test that ConfigFileDiscovery expands {appname} in patterns.
    """
    temp_dir = tempfile.mkdtemp()
    
    try:
        # Create app-specific config file
        myapp_yaml = Path(temp_dir) / "myapp.yaml"
        myapp_yaml.write_text("key: value")
        
        discovery = ConfigFileDiscovery(
            appname="myapp",
            search_directories=[temp_dir],
            file_patterns=["{appname}.*"]
        )
        
        files = discovery.discover()
        filenames = [f.name for f in files]
        
        if "myapp.yaml" not in filenames:
            errmsg = f"Expected 'myapp.yaml' in discovered files, got {filenames}"
            raise AssertionError(errmsg)
    
    finally:
        shutil.rmtree(temp_dir)
    
    return


def test_config_file_discovery_environment_specific():
    """
        Test that ConfigFileDiscovery discovers environment-specific files.
    """
    temp_dir = tempfile.mkdtemp()
    
    try:
        # Create base and environment-specific config files
        settings_yaml = Path(temp_dir) / "settings.yaml"
        settings_yaml.write_text("env: base")
        
        settings_prod_yaml = Path(temp_dir) / "settings.production.yaml"
        settings_prod_yaml.write_text("env: production")
        
        discovery = ConfigFileDiscovery(
            appname="testapp",
            search_directories=[temp_dir],
            environment="production"
        )
        
        files = discovery.discover()
        filenames = [f.name for f in files]
        
        # Should find both base and environment-specific files
        if "settings.yaml" not in filenames:
            errmsg = f"Expected 'settings.yaml' in discovered files, got {filenames}"
            raise AssertionError(errmsg)
        
        if "settings.production.yaml" not in filenames:
            errmsg = f"Expected 'settings.production.yaml' in discovered files, got {filenames}"
            raise AssertionError(errmsg)
        
        # Environment-specific file should come after base file (higher precedence)
        base_idx = filenames.index("settings.yaml")
        env_idx = filenames.index("settings.production.yaml")
        
        if env_idx <= base_idx:
            errmsg = f"Expected environment file after base file, got base at {base_idx}, env at {env_idx}"
            raise AssertionError(errmsg)
    
    finally:
        shutil.rmtree(temp_dir)
    
    return


def test_config_file_discovery_profile_from_env_var():
    """
        Test that ConfigFileDiscovery reads profile from environment variable.
    """
    env_vars = {"TEST_PROFILE_VAR": "staging"}
    
    try:
        set_test_env_vars(env_vars)
        
        discovery = ConfigFileDiscovery(
            appname="testapp",
            profile_env_var="TEST_PROFILE_VAR"
        )
        
        if discovery.profile != "staging":
            errmsg = f"Expected profile 'staging', got {discovery.profile}"
            raise AssertionError(errmsg)
    
    finally:
        clear_test_env_vars(env_vars)
    
    return


def test_config_file_discovery_explicit_profile_overrides_env():
    """
        Test that explicit profile overrides environment variable.
    """
    env_vars = {"TEST_PROFILE_VAR2": "staging"}
    
    try:
        set_test_env_vars(env_vars)
        
        discovery = ConfigFileDiscovery(
            appname="testapp",
            profile="production",
            profile_env_var="TEST_PROFILE_VAR2"
        )
        
        if discovery.profile != "production":
            errmsg = f"Expected profile 'production', got {discovery.profile}"
            raise AssertionError(errmsg)
    
    finally:
        clear_test_env_vars(env_vars)
    
    return


def test_config_file_discovery_create_file_source():
    """
        Test that ConfigFileDiscovery can create a FileSource.
    """
    temp_dir = tempfile.mkdtemp()
    
    try:
        # Create a config file
        settings_yaml = Path(temp_dir) / "settings.yaml"
        settings_yaml.write_text("database:\n  host: localhost")
        
        discovery = ConfigFileDiscovery(
            appname="testapp",
            search_directories=[temp_dir]
        )
        
        file_source = discovery.create_file_source()
        
        if file_source is None:
            errmsg = "Expected FileSource, got None"
            raise AssertionError(errmsg)
        
        # Load configuration
        config = file_source.load()
        
        if config.get("database.host") != "localhost":
            errmsg = f"Expected database.host='localhost', got {config.get('database.host')}"
            raise AssertionError(errmsg)
    
    finally:
        shutil.rmtree(temp_dir)
    
    return


# =============================================================================
# Property-Based Tests for File Discovery
# =============================================================================

# Feature: configuration-system, Property 17: File Discovery
# *For any* configured search directory and file name pattern, configuration
# files matching the pattern in those directories SHALL be discovered and loaded.
# **Validates: Requirements 5.1, 5.3**

def test_property_17_file_discovery():
    """
        Property 17: File Discovery
        
        For any configured search directory and file name pattern, configuration
        files matching the pattern in those directories SHALL be discovered
        and loaded.
        
        **Feature: configuration-system, Property 17: File Discovery**
        **Validates: Requirements 5.1, 5.3**
    """
    # Run 100 iterations with random data
    for iteration in range(100):
        temp_dir = tempfile.mkdtemp()
        
        try:
            # Generate random appname
            appname = generate_random_key_part(3, 8)
            
            # Generate random number of config files
            num_files = random.randint(1, 5)
            expected_files: List[str] = []
            
            # Supported formats for this test
            formats = ["yaml", "json", "ini"]
            
            for i in range(num_files):
                # Choose a random pattern type
                pattern_type = random.choice(["settings", "config", "appname"])
                fmt = random.choice(formats)
                
                if pattern_type == "settings":
                    filename = f"settings.{fmt}"
                elif pattern_type == "config":
                    filename = f"config.{fmt}"
                else:
                    filename = f"{appname}.{fmt}"
                
                # Create the file
                file_path = Path(temp_dir) / filename
                
                if fmt == "yaml":
                    file_path.write_text(f"key{i}: value{i}")
                elif fmt == "json":
                    file_path.write_text(f'{{"key{i}": "value{i}"}}')
                else:  # ini
                    file_path.write_text(f"[section{i}]\nkey{i} = value{i}")
                
                if filename not in expected_files:
                    expected_files.append(filename)
            
            # Create discovery
            discovery = ConfigFileDiscovery(
                appname=appname,
                search_directories=[temp_dir]
            )
            
            # Discover files
            files = discovery.discover()
            discovered_names = [f.name for f in files]
            
            # Verify all expected files are discovered
            for expected in expected_files:
                if expected not in discovered_names:
                    errmsg = f"Iteration {iteration}: Expected '{expected}' in discovered files, got {discovered_names}"
                    raise AssertionError(errmsg)
        
        finally:
            shutil.rmtree(temp_dir)
    
    return


def test_property_17_file_discovery_multiple_directories():
    """
        Property 17 (Extended): File Discovery Across Multiple Directories
        
        For any set of search directories, files from all directories
        SHALL be discovered.
        
        **Feature: configuration-system, Property 17: File Discovery**
        **Validates: Requirements 5.1, 5.3**
    """
    # Run 50 iterations with random data
    for iteration in range(50):
        temp_dirs = [tempfile.mkdtemp() for _ in range(random.randint(2, 4))]
        
        try:
            expected_files: List[str] = []
            
            # Create files in each directory
            for i, temp_dir in enumerate(temp_dirs):
                filename = f"settings{i}.yaml"
                file_path = Path(temp_dir) / filename
                file_path.write_text(f"dir: {i}")
                expected_files.append(filename)
            
            # Create discovery with multiple directories
            discovery = ConfigFileDiscovery(
                appname="testapp",
                search_directories=temp_dirs,
                file_patterns=["settings*.yaml"]
            )
            
            # Discover files
            files = discovery.discover()
            discovered_names = [f.name for f in files]
            
            # Verify files from all directories are discovered
            for expected in expected_files:
                if expected not in discovered_names:
                    errmsg = f"Iteration {iteration}: Expected '{expected}' in discovered files, got {discovered_names}"
                    raise AssertionError(errmsg)
        
        finally:
            for temp_dir in temp_dirs:
                shutil.rmtree(temp_dir)
    
    return


def test_property_17_file_discovery_pattern_matching():
    """
        Property 17 (Extended): File Discovery Pattern Matching
        
        For any file pattern, only files matching that pattern SHALL be
        discovered.
        
        **Feature: configuration-system, Property 17: File Discovery**
        **Validates: Requirements 5.1, 5.3**
    """
    # Run 50 iterations with random data
    for iteration in range(50):
        temp_dir = tempfile.mkdtemp()
        
        try:
            # Create matching and non-matching files
            matching_file = Path(temp_dir) / "settings.yaml"
            matching_file.write_text("key: value")
            
            non_matching_file = Path(temp_dir) / "other.yaml"
            non_matching_file.write_text("key: value")
            
            # Create discovery with specific pattern
            discovery = ConfigFileDiscovery(
                appname="testapp",
                search_directories=[temp_dir],
                file_patterns=["settings.*"]
            )
            
            # Discover files
            files = discovery.discover()
            discovered_names = [f.name for f in files]
            
            # Verify matching file is discovered
            if "settings.yaml" not in discovered_names:
                errmsg = f"Iteration {iteration}: Expected 'settings.yaml' in discovered files, got {discovered_names}"
                raise AssertionError(errmsg)
            
            # Verify non-matching file is NOT discovered
            if "other.yaml" in discovered_names:
                errmsg = f"Iteration {iteration}: Did not expect 'other.yaml' in discovered files, got {discovered_names}"
                raise AssertionError(errmsg)
        
        finally:
            shutil.rmtree(temp_dir)
    
    return


# =============================================================================
# Property-Based Tests for Environment-Specific Files
# =============================================================================

# Feature: configuration-system, Property 18: Environment-Specific Files
# *For any* active environment/profile, the corresponding environment-specific
# configuration file (e.g., settings.production.yaml) SHALL be loaded and
# merged with the base configuration.
# **Validates: Requirements 5.4**

def test_property_18_environment_specific_files():
    """
        Property 18: Environment-Specific Files
        
        For any active environment, the corresponding environment-specific
        configuration file (e.g., settings.production.yaml) SHALL be loaded
        and merged with the base configuration.
        
        **Feature: configuration-system, Property 18: Environment-Specific Files**
        **Validates: Requirements 5.4**
    """
    # Test with various environments
    environments = ["production", "development", "staging", "test", "local"]
    
    for iteration, environment in enumerate(environments):
        temp_dir = tempfile.mkdtemp()
        
        try:
            # Generate random base values
            base_key = generate_random_key_part()
            base_value = generate_random_value()
            env_value = generate_random_value()
            
            # Create base config file
            base_file = Path(temp_dir) / "settings.yaml"
            base_file.write_text(f"'{base_key}': '{base_value}'\nenv: base")
            
            # Create environment-specific config file
            env_file = Path(temp_dir) / f"settings.{environment}.yaml"
            env_file.write_text(f"'{base_key}': '{env_value}'\nenv: {environment}")
            
            # Create discovery with environment
            discovery = ConfigFileDiscovery(
                appname="testapp",
                search_directories=[temp_dir],
                environment=environment
            )
            
            # Create FileSource and load
            file_source = discovery.create_file_source()
            config = file_source.load()
            
            # Verify environment-specific value overrides base
            if config.get(base_key) != env_value:
                errmsg = f"Environment '{environment}': Expected '{base_key}'='{env_value}', got '{config.get(base_key)}'"
                raise AssertionError(errmsg)
            
            # Verify env marker is from environment-specific file
            if config.get("env") != environment:
                errmsg = f"Environment '{environment}': Expected env='{environment}', got '{config.get('env')}'"
                raise AssertionError(errmsg)
        
        finally:
            shutil.rmtree(temp_dir)
    
    return


def test_property_18_environment_specific_files_random():
    """
        Property 18 (Extended): Environment-Specific Files with Random Data
        
        For any randomly generated environment name and configuration,
        environment-specific files SHALL be correctly discovered and merged.
        
        **Feature: configuration-system, Property 18: Environment-Specific Files**
        **Validates: Requirements 5.4**
    """
    # Run 50 iterations with random data
    for iteration in range(50):
        temp_dir = tempfile.mkdtemp()
        
        try:
            # Generate random environment name
            environment = generate_random_key_part(4, 10)
            
            # Generate random config keys and values
            num_keys = random.randint(1, 5)
            base_config: Dict[str, str] = {}
            env_config: Dict[str, str] = {}
            
            for _ in range(num_keys):
                key = generate_random_key_part()
                base_config[key] = generate_random_value()
                # Some keys will be overridden, some won't
                if random.choice([True, False]):
                    env_config[key] = generate_random_value()
            
            # Create base config file
            base_content = "\n".join(f"'{k}': '{v}'" for k, v in base_config.items())
            base_file = Path(temp_dir) / "settings.yaml"
            base_file.write_text(base_content)
            
            # Create environment-specific config file
            env_content = "\n".join(f"'{k}': '{v}'" for k, v in env_config.items())
            env_file = Path(temp_dir) / f"settings.{environment}.yaml"
            env_file.write_text(env_content)
            
            # Create discovery with environment
            discovery = ConfigFileDiscovery(
                appname="testapp",
                search_directories=[temp_dir],
                environment=environment
            )
            
            # Create FileSource and load
            file_source = discovery.create_file_source()
            config = file_source.load()
            
            # Verify merged configuration
            for key in base_config:
                expected_value = env_config.get(key, base_config[key])
                actual_value = config.get(key)
                
                if actual_value != expected_value:
                    errmsg = f"Iteration {iteration}: Expected '{key}'='{expected_value}', got '{actual_value}'"
                    raise AssertionError(errmsg)
        
        finally:
            shutil.rmtree(temp_dir)
    
    return


def test_property_18_environment_specific_files_precedence():
    """
        Property 18 (Extended): Environment-Specific Files Precedence
        
        Environment-specific files SHALL take precedence over base files
        for the same keys.
        
        **Feature: configuration-system, Property 18: Environment-Specific Files**
        **Validates: Requirements 5.4**
    """
    # Run 50 iterations with random data
    for iteration in range(50):
        temp_dir = tempfile.mkdtemp()
        
        try:
            environment = generate_random_key_part(4, 8)
            
            # Create a key that exists in both files
            shared_key = generate_random_key_part()
            base_value = f"base_{generate_random_value()}"
            env_value = f"env_{generate_random_value()}"
            
            # Create base config file
            base_file = Path(temp_dir) / "settings.yaml"
            base_file.write_text(f"'{shared_key}': '{base_value}'")
            
            # Create environment-specific config file
            env_file = Path(temp_dir) / f"settings.{environment}.yaml"
            env_file.write_text(f"'{shared_key}': '{env_value}'")
            
            # Create discovery with environment
            discovery = ConfigFileDiscovery(
                appname="testapp",
                search_directories=[temp_dir],
                environment=environment
            )
            
            # Create FileSource and load
            file_source = discovery.create_file_source()
            config = file_source.load()
            
            # Verify environment-specific value takes precedence
            if config.get(shared_key) != env_value:
                errmsg = f"Iteration {iteration}: Expected '{shared_key}'='{env_value}', got '{config.get(shared_key)}'"
                raise AssertionError(errmsg)
        
        finally:
            shutil.rmtree(temp_dir)
    
    return

# =============================================================================
# Property-Based Tests for File Merge Precedence
# =============================================================================

# Feature: configuration-system, Property 19: File Merge Precedence
# *For any* set of configuration files with overlapping keys, the files
# SHALL be merged according to the configured precedence order.
# **Validates: Requirements 5.5**

def test_property_19_file_merge_precedence():
    """
        Property 19: File Merge Precedence
        
        For any set of configuration files with overlapping keys, the files
        SHALL be merged according to the configured precedence order.
        
        **Feature: configuration-system, Property 19: File Merge Precedence**
        **Validates: Requirements 5.5**
    """
    # Run 50 iterations with random data
    for iteration in range(50):
        temp_dirs = [tempfile.mkdtemp() for _ in range(3)]
        
        try:
            # Generate a shared key that will be in all files
            shared_key = generate_random_key_part()
            
            # Create config files in each directory with different values
            values = []
            for i, temp_dir in enumerate(temp_dirs):
                value = f"dir{i}_{generate_random_value()}"
                values.append(value)
                
                config_file = Path(temp_dir) / "settings.yaml"
                config_file.write_text(f"'{shared_key}': '{value}'")
            
            # Create discovery with directories in order
            discovery = ConfigFileDiscovery(
                appname="testapp",
                search_directories=temp_dirs
            )
            
            # Create FileSource and load
            file_source = discovery.create_file_source()
            config = file_source.load()
            
            # The last directory's value should win (later directories have higher precedence)
            expected_value = values[-1]
            actual_value = config.get(shared_key)
            
            if actual_value != expected_value:
                errmsg = f"Iteration {iteration}: Expected '{shared_key}'='{expected_value}', got '{actual_value}'"
                raise AssertionError(errmsg)
        
        finally:
            for temp_dir in temp_dirs:
                shutil.rmtree(temp_dir)
    
    return


def test_property_19_file_merge_precedence_env_over_base():
    """
        Property 19 (Extended): Environment Files Take Precedence Over Base
        
        Environment-specific files SHALL take precedence over base files.
        
        **Feature: configuration-system, Property 19: File Merge Precedence**
        **Validates: Requirements 5.5**
    """
    # Run 50 iterations with random data
    for iteration in range(50):
        temp_dir = tempfile.mkdtemp()
        
        try:
            environment = generate_random_key_part(4, 8)
            shared_key = generate_random_key_part()
            
            base_value = f"base_{generate_random_value()}"
            env_value = f"env_{generate_random_value()}"
            
            base_file = Path(temp_dir) / "settings.yaml"
            base_file.write_text(f"'{shared_key}': '{base_value}'")
            
            env_file = Path(temp_dir) / f"settings.{environment}.yaml"
            env_file.write_text(f"'{shared_key}': '{env_value}'")
            
            discovery = ConfigFileDiscovery(
                appname="testapp",
                search_directories=[temp_dir],
                environment=environment
            )
            
            file_source = discovery.create_file_source()
            config = file_source.load()
            
            if config.get(shared_key) != env_value:
                errmsg = f"Iteration {iteration}: Expected env value '{env_value}', got '{config.get(shared_key)}'"
                raise AssertionError(errmsg)
        
        finally:
            shutil.rmtree(temp_dir)
    
    return


def test_property_19_file_merge_precedence_profile_over_env():
    """
        Property 19 (Extended): Profile Files Take Precedence Over Environment
        
        Profile-specific files SHALL take precedence over environment-specific files.
        
        **Feature: configuration-system, Property 19: File Merge Precedence**
        **Validates: Requirements 5.5**
    """
    # Run 50 iterations with random data
    for iteration in range(50):
        temp_dir = tempfile.mkdtemp()
        
        try:
            environment = generate_random_key_part(4, 8)
            profile = generate_random_key_part(4, 8)
            shared_key = generate_random_key_part()
            
            base_value = f"base_{generate_random_value()}"
            env_value = f"env_{generate_random_value()}"
            profile_value = f"profile_{generate_random_value()}"
            
            base_file = Path(temp_dir) / "settings.yaml"
            base_file.write_text(f"'{shared_key}': '{base_value}'")
            
            env_file = Path(temp_dir) / f"settings.{environment}.yaml"
            env_file.write_text(f"'{shared_key}': '{env_value}'")
            
            profile_file = Path(temp_dir) / f"settings.{profile}.yaml"
            profile_file.write_text(f"'{shared_key}': '{profile_value}'")
            
            discovery = ConfigFileDiscovery(
                appname="testapp",
                search_directories=[temp_dir],
                environment=environment,
                profile=profile
            )
            
            file_source = discovery.create_file_source()
            config = file_source.load()
            
            if config.get(shared_key) != profile_value:
                errmsg = f"Iteration {iteration}: Expected profile value '{profile_value}', got '{config.get(shared_key)}'"
                raise AssertionError(errmsg)
        
        finally:
            shutil.rmtree(temp_dir)
    
    return

# =============================================================================
# Property-Based Tests for Profile Configuration
# =============================================================================

# Feature: configuration-system, Property 31: Profile Configuration
# *For any* active profile selected via environment variable, the profile-specific
# configuration SHALL be loaded and merged with base configuration, with profile
# values taking precedence.
# **Validates: Requirements 8.6, 8.7, 8.8**

def test_property_31_profile_configuration():
    """
        Property 31: Profile Configuration
        
        For any active profile selected via environment variable, the profile-specific
        configuration SHALL be loaded and merged with base configuration, with profile
        values taking precedence.
        
        **Feature: configuration-system, Property 31: Profile Configuration**
        **Validates: Requirements 8.6, 8.7, 8.8**
    """
    # Run 50 iterations with random data
    for iteration in range(50):
        temp_dir = tempfile.mkdtemp()
        profile_env_var = f"TEST_PROFILE_{iteration}"
        
        try:
            # Generate random profile name
            profile = generate_random_key_part(4, 10)
            
            # Set profile via environment variable
            os.environ[profile_env_var] = profile
            
            # Generate random config keys and values
            shared_key = generate_random_key_part()
            base_value = f"base_{generate_random_value()}"
            profile_value = f"profile_{generate_random_value()}"
            
            # Create base config file
            base_file = Path(temp_dir) / "settings.yaml"
            base_file.write_text(f"'{shared_key}': '{base_value}'")
            
            # Create profile-specific config file
            profile_file = Path(temp_dir) / f"settings.{profile}.yaml"
            profile_file.write_text(f"'{shared_key}': '{profile_value}'")
            
            # Create discovery with profile from environment variable
            discovery = ConfigFileDiscovery(
                appname="testapp",
                search_directories=[temp_dir],
                profile_env_var=profile_env_var
            )
            
            # Verify profile is read from environment variable
            if discovery.profile != profile:
                errmsg = f"Iteration {iteration}: Expected profile '{profile}', got '{discovery.profile}'"
                raise AssertionError(errmsg)
            
            # Create FileSource and load
            file_source = discovery.create_file_source()
            config = file_source.load()
            
            # Verify profile-specific value takes precedence
            if config.get(shared_key) != profile_value:
                errmsg = f"Iteration {iteration}: Expected '{shared_key}'='{profile_value}', got '{config.get(shared_key)}'"
                raise AssertionError(errmsg)
        
        finally:
            if profile_env_var in os.environ:
                del os.environ[profile_env_var]
            shutil.rmtree(temp_dir)
    
    return


def test_property_31_profile_configuration_explicit():
    """
        Property 31 (Extended): Explicit Profile Configuration
        
        For any explicitly set profile, the profile-specific configuration
        SHALL be loaded and merged with base configuration.
        
        **Feature: configuration-system, Property 31: Profile Configuration**
        **Validates: Requirements 8.6, 8.7, 8.8**
    """
    # Run 50 iterations with random data
    for iteration in range(50):
        temp_dir = tempfile.mkdtemp()
        
        try:
            # Generate random profile name
            profile = generate_random_key_part(4, 10)
            
            # Generate random config keys and values
            num_keys = random.randint(1, 5)
            base_config: Dict[str, str] = {}
            profile_config: Dict[str, str] = {}
            
            for _ in range(num_keys):
                key = generate_random_key_part()
                base_config[key] = f"base_{generate_random_value()}"
                # Some keys will be overridden, some won't
                if random.choice([True, False]):
                    profile_config[key] = f"profile_{generate_random_value()}"
            
            # Create base config file
            base_content = "\n".join(f"'{k}': '{v}'" for k, v in base_config.items())
            base_file = Path(temp_dir) / "settings.yaml"
            base_file.write_text(base_content)
            
            # Create profile-specific config file
            profile_content = "\n".join(f"'{k}': '{v}'" for k, v in profile_config.items())
            profile_file = Path(temp_dir) / f"settings.{profile}.yaml"
            profile_file.write_text(profile_content)
            
            # Create discovery with explicit profile
            discovery = ConfigFileDiscovery(
                appname="testapp",
                search_directories=[temp_dir],
                profile=profile
            )
            
            # Create FileSource and load
            file_source = discovery.create_file_source()
            config = file_source.load()
            
            # Verify merged configuration
            for key in base_config:
                expected_value = profile_config.get(key, base_config[key])
                actual_value = config.get(key)
                
                if actual_value != expected_value:
                    errmsg = f"Iteration {iteration}: Expected '{key}'='{expected_value}', got '{actual_value}'"
                    raise AssertionError(errmsg)
        
        finally:
            shutil.rmtree(temp_dir)
    
    return


def test_property_31_profile_configuration_precedence():
    """
        Property 31 (Extended): Profile Configuration Precedence
        
        Profile-specific configuration SHALL take precedence over base
        configuration for the same keys.
        
        **Feature: configuration-system, Property 31: Profile Configuration**
        **Validates: Requirements 8.6, 8.7, 8.8**
    """
    # Run 50 iterations with random data
    for iteration in range(50):
        temp_dir = tempfile.mkdtemp()
        
        try:
            profile = generate_random_key_part(4, 8)
            shared_key = generate_random_key_part()
            
            base_value = f"base_{generate_random_value()}"
            profile_value = f"profile_{generate_random_value()}"
            
            # Create base config file
            base_file = Path(temp_dir) / "settings.yaml"
            base_file.write_text(f"'{shared_key}': '{base_value}'")
            
            # Create profile-specific config file
            profile_file = Path(temp_dir) / f"settings.{profile}.yaml"
            profile_file.write_text(f"'{shared_key}': '{profile_value}'")
            
            # Create discovery with profile
            discovery = ConfigFileDiscovery(
                appname="testapp",
                search_directories=[temp_dir],
                profile=profile
            )
            
            # Create FileSource and load
            file_source = discovery.create_file_source()
            config = file_source.load()
            
            # Verify profile value takes precedence
            if config.get(shared_key) != profile_value:
                errmsg = f"Iteration {iteration}: Expected profile value '{profile_value}', got '{config.get(shared_key)}'"
                raise AssertionError(errmsg)
        
        finally:
            shutil.rmtree(temp_dir)
    
    return


# =============================================================================
# Environment names are matched to keys that contain the separator
# =============================================================================

def _load_with_environment(source: ConfigSource, variables: Dict[str, str]) -> Dict[str, Any]:
    """
        Load a source with some environment variables set, and remove them
        again afterwards.
        
        :param source: The source to load.
        :param variables: The environment variables to set for the load.
        
        :returns: What the source loaded.
    """
    for name, value in variables.items():
        os.environ[name] = value
    
    try:
        loaded = source.load()
    finally:
        for name in variables:
            del os.environ[name]
    
    return loaded


def test_environment_source_resolves_name_against_known_keys():
    """
        Test that a variable name is mapped to the schema key it spells when
        that key contains the separator.
    """
    source = EnvironmentSource(prefix="WWTEST_KNOWN_")
    source.use_known_keys(["database.max_connections", "database.host"])
    
    loaded = _load_with_environment(source, {
        "WWTEST_KNOWN_DATABASE_MAX_CONNECTIONS": "50",
        "WWTEST_KNOWN_DATABASE_HOST": "db.example.com",
    })
    
    expected = {"database.max_connections": "50", "database.host": "db.example.com"}
    if loaded != expected:
        errmsg = f"Expected {expected}, got {loaded}"
        raise AssertionError(errmsg)
    
    return


def test_environment_source_without_known_keys_maps_every_separator_to_a_dot():
    """
        Test that without schema keys every separator still becomes a dot.
    """
    source = EnvironmentSource(prefix="WWTEST_PLAIN_")
    
    loaded = _load_with_environment(source, {"WWTEST_PLAIN_DATABASE_MAX_CONNECTIONS": "50"})
    
    if loaded != {"database.max.connections": "50"}:
        errmsg = f"Expected the fully dotted key, got {loaded}"
        raise AssertionError(errmsg)
    
    return


def test_environment_source_doubled_separator_marks_nesting():
    """
        Test that a doubled separator separates the nesting levels and keeps
        single separators in the key.
    """
    source = EnvironmentSource(prefix="WWTEST_DOUBLE_")
    
    loaded = _load_with_environment(source, {"WWTEST_DOUBLE_DATABASE__MAX_CONNECTIONS": "50"})
    
    if loaded != {"database.max_connections": "50"}:
        errmsg = f"Expected 'database.max_connections', got {loaded}"
        raise AssertionError(errmsg)
    
    return


def test_environment_source_ambiguous_known_keys_keep_the_dotted_key():
    """
        Test that a name that spells two schema keys is not resolved to
        either of them.
    """
    source = EnvironmentSource(prefix="WWTEST_AMBIG_")
    source.use_known_keys(["cache.max_size", "cache_max.size"])
    
    loaded = _load_with_environment(source, {"WWTEST_AMBIG_CACHE_MAX_SIZE": "9"})
    
    if loaded != {"cache.max.size": "9"}:
        errmsg = f"Expected the fully dotted key, got {loaded}"
        raise AssertionError(errmsg)
    
    return


def test_environment_variable_overrides_schema_key_with_underscore():
    """
        Test that, through the registry, an environment variable overrides a
        schema key whose name contains an underscore.
    """
    from ccai.webworks.configuration import ConfigRegistry, ConfigSchema
    
    schema = ConfigSchema()
    schema.define("database.max_connections", int, default=10)
    
    registry = ConfigRegistry(schema=schema)
    registry.register_source(EnvironmentSource(prefix="WWTEST_REG_"))
    
    os.environ["WWTEST_REG_DATABASE_MAX_CONNECTIONS"] = "50"
    try:
        registry.load()
    finally:
        del os.environ["WWTEST_REG_DATABASE_MAX_CONNECTIONS"]
    
    if registry.get("database.max_connections") != 50:
        errmsg = f"Expected 50, got {registry.get('database.max_connections')!r}"
        raise AssertionError(errmsg)
    
    if "database.max.connections" in registry.keys():
        errmsg = "The variable should not also create 'database.max.connections'"
        raise AssertionError(errmsg)
    
    return


def test_secrets_provider_resolves_name_against_known_keys():
    """
        Test that SECRET_API_KEY sets 'api_key' when the schema defines it.
    """
    provider = SecretsProvider(env_prefix="WWTEST_SECRET_")
    provider.use_known_keys(["api_key"])
    
    loaded = _load_with_environment(provider, {"WWTEST_SECRET_API_KEY": "s3cret"})
    
    if list(loaded.keys()) != ["api_key"]:
        errmsg = f"Expected the key 'api_key', got {list(loaded.keys())}"
        raise AssertionError(errmsg)
    
    if loaded["api_key"].get_secret_value() != "s3cret":
        errmsg = "Expected the secret value to be loaded"
        raise AssertionError(errmsg)
    
    return


# =============================================================================
# INI values are literal and sections keep their own keys
# =============================================================================

def test_ini_loader_keeps_percent_sign_in_value():
    """
        Test that a '%' in a value is read as it is.
    """
    loader = IniLoader()
    
    result = loader.load("[db]\npassword = abc%def\nformat = %(name)s\n")
    
    expected = {"db.password": "abc%def", "db.format": "%(name)s"}
    if result != expected:
        errmsg = f"Expected {expected}, got {result}"
        raise AssertionError(errmsg)
    
    return


def test_ini_loader_keeps_section_override_of_default_key():
    """
        Test that a section's own value for a key that [DEFAULT] also defines
        is kept.
    """
    loader = IniLoader()
    
    result = loader.load("[DEFAULT]\nhost = localhost\n\n[db]\nhost = db.example.com\n")
    
    expected = {"host": "localhost", "db.host": "db.example.com"}
    if result != expected:
        errmsg = f"Expected {expected}, got {result}"
        raise AssertionError(errmsg)
    
    return


def test_ini_loader_does_not_copy_default_keys_into_sections():
    """
        Test that a [DEFAULT] key is a top-level key only.
    """
    loader = IniLoader()
    
    result = loader.load("[DEFAULT]\nhost = localhost\n\n[db]\nport = 5432\n")
    
    expected = {"host": "localhost", "db.port": "5432"}
    if result != expected:
        errmsg = f"Expected {expected}, got {result}"
        raise AssertionError(errmsg)
    
    return


def test_ini_loader_round_trips_percent_sign():
    """
        Test that dump() writes a value with '%' that load() reads back.
    """
    loader = IniLoader()
    data = {"db.password": "abc%def", "name": "100%"}
    
    result = loader.load(loader.dump(data))
    
    if result != data:
        errmsg = f"Expected {data}, got {result}"
        raise AssertionError(errmsg)
    
    return


# =============================================================================
# Include directives
# =============================================================================

def test_file_source_unquoted_include_stops_at_end_of_line():
    """
        Test that an unquoted include path does not take in the lines after it.
    """
    temp_dir = tempfile.mkdtemp()
    
    try:
        (Path(temp_dir) / "base.ini").write_text("[logging]\nlevel = DEBUG\n")
        main_path = Path(temp_dir) / "main.ini"
        main_path.write_text("%include base.ini\n[database]\nhost = localhost\n")
        
        result = FileSource(paths=[main_path]).load()
        
        expected = {"logging.level": "DEBUG", "database.host": "localhost"}
        if result != expected:
            errmsg = f"Expected {expected}, got {result}"
            raise AssertionError(errmsg)
    finally:
        shutil.rmtree(temp_dir)
    
    return


def test_file_source_include_directive_in_cfg_and_conf_files():
    """
        Test that .cfg and .conf files use the INI include directive.
    """
    temp_dir = tempfile.mkdtemp()
    
    try:
        (Path(temp_dir) / "base.ini").write_text("[logging]\nlevel = DEBUG\n")
        
        for extension in ("cfg", "conf"):
            main_path = Path(temp_dir) / f"main.{extension}"
            main_path.write_text("%include base.ini\n[database]\nhost = localhost\n")
            
            result = FileSource(paths=[main_path]).load()
            
            if result.get("logging.level") != "DEBUG":
                errmsg = f"Expected the include of a .{extension} file to be processed, got {result}"
                raise AssertionError(errmsg)
    finally:
        shutil.rmtree(temp_dir)
    
    return


def test_file_source_include_directive_in_yml_file():
    """
        Test that a .yml file uses the YAML include directive.
    """
    if not YAML_AVAILABLE:
        return  # Skip if YAML not available
    
    temp_dir = tempfile.mkdtemp()
    
    try:
        (Path(temp_dir) / "base.yaml").write_text("logging:\n  level: DEBUG\n")
        main_path = Path(temp_dir) / "main.yml"
        main_path.write_text("# !include base.yaml\ndatabase:\n  host: localhost\n")
        
        result = FileSource(paths=[main_path]).load()
        
        expected = {"logging.level": "DEBUG", "database.host": "localhost"}
        if result != expected:
            errmsg = f"Expected {expected}, got {result}"
            raise AssertionError(errmsg)
    finally:
        shutil.rmtree(temp_dir)
    
    return


def test_file_source_include_merges_mapping_with_same_top_level_key():
    """
        Test that an included mapping is merged with a mapping of the same
        name in the including file instead of being replaced by it.
    """
    if not YAML_AVAILABLE:
        return  # Skip if YAML not available
    
    temp_dir = tempfile.mkdtemp()
    
    try:
        (Path(temp_dir) / "base.yaml").write_text("database:\n  host: basehost\n  port: 5432\n")
        main_path = Path(temp_dir) / "main.yaml"
        main_path.write_text("# !include base.yaml\ndatabase:\n  port: 6543\n")
        
        result = FileSource(paths=[main_path]).load()
        
        expected = {"database.host": "basehost", "database.port": 6543}
        if result != expected:
            errmsg = f"Expected {expected}, got {result}"
            raise AssertionError(errmsg)
    finally:
        shutil.rmtree(temp_dir)
    
    return


def test_file_source_include_after_settings_overrides_them():
    """
        Test that an include placed after the file's own settings takes
        precedence over them.
    """
    temp_dir = tempfile.mkdtemp()
    
    try:
        (Path(temp_dir) / "override.ini").write_text("[database]\nhost = overridden\n")
        main_path = Path(temp_dir) / "main.ini"
        main_path.write_text("[database]\nhost = localhost\nport = 5432\n%include override.ini\n")
        
        result = FileSource(paths=[main_path]).load()
        
        expected = {"database.host": "overridden", "database.port": "5432"}
        if result != expected:
            errmsg = f"Expected {expected}, got {result}"
            raise AssertionError(errmsg)
    finally:
        shutil.rmtree(temp_dir)
    
    return


def test_file_source_diamond_include_is_not_circular():
    """
        Test that a file included from two files is loaded, not reported as
        a circular include.
    """
    temp_dir = tempfile.mkdtemp()
    
    try:
        (Path(temp_dir) / "shared.ini").write_text("[shared]\nvalue = 1\n")
        (Path(temp_dir) / "left.ini").write_text("%include shared.ini\n[left]\nvalue = 2\n")
        (Path(temp_dir) / "right.ini").write_text("%include shared.ini\n[right]\nvalue = 3\n")
        main_path = Path(temp_dir) / "main.ini"
        main_path.write_text("%include left.ini\n%include right.ini\n")
        
        result = FileSource(paths=[main_path]).load()
        
        expected = {"shared.value": "1", "left.value": "2", "right.value": "3"}
        if result != expected:
            errmsg = f"Expected {expected}, got {result}"
            raise AssertionError(errmsg)
    finally:
        shutil.rmtree(temp_dir)
    
    return


def test_file_source_include_of_itself_through_another_file_is_circular():
    """
        Test that two files that include each other are reported as a
        circular include.
    """
    temp_dir = tempfile.mkdtemp()
    
    try:
        (Path(temp_dir) / "a.ini").write_text("%include b.ini\n[a]\nvalue = 1\n")
        (Path(temp_dir) / "b.ini").write_text("%include a.ini\n[b]\nvalue = 2\n")
        
        try:
            FileSource(paths=[Path(temp_dir) / "a.ini"]).load()
            errmsg = "Expected ConfigurationError for a circular include"
            raise AssertionError(errmsg)
        except ConfigurationFileNotFoundError:
            raise
        except ConfigurationError as exc:
            if "Circular include" not in str(exc):
                errmsg = f"Expected a circular include error, got {exc}"
                raise AssertionError(errmsg)
    finally:
        shutil.rmtree(temp_dir)
    
    return


def test_file_source_includes_file_of_another_format():
    """
        Test that an included file is read in the format of its own extension.
    """
    temp_dir = tempfile.mkdtemp()
    
    try:
        (Path(temp_dir) / "base.json").write_text('{"logging": {"level": "DEBUG"}}')
        main_path = Path(temp_dir) / "main.ini"
        main_path.write_text("%include base.json\n[database]\nhost = localhost\n")
        
        result = FileSource(paths=[main_path]).load()
        
        expected = {"logging.level": "DEBUG", "database.host": "localhost"}
        if result != expected:
            errmsg = f"Expected {expected}, got {result}"
            raise AssertionError(errmsg)
    finally:
        shutil.rmtree(temp_dir)
    
    return


# =============================================================================
# A configured secrets file must exist
# =============================================================================

def test_secrets_provider_missing_secrets_file_raises():
    """
        Test that load() raises when the configured secrets file is missing.
    """
    temp_dir = tempfile.mkdtemp()
    
    try:
        provider = SecretsProvider(
            env_prefix="WWTEST_NOSECRETS_",
            secrets_file=Path(temp_dir) / "missing.enc",
            encryption_key=b"0123456789abcdef0123456789abcdef"
        )
        
        try:
            provider.load()
            errmsg = "Expected ConfigurationFileNotFoundError for a missing secrets file"
            raise AssertionError(errmsg)
        except ConfigurationFileNotFoundError:
            pass  # Expected
    finally:
        shutil.rmtree(temp_dir)
    
    return


def test_secrets_provider_optional_secrets_file_may_be_missing():
    """
        Test that a secrets file declared optional may be absent.
    """
    temp_dir = tempfile.mkdtemp()
    
    try:
        provider = SecretsProvider(
            env_prefix="WWTEST_NOSECRETS_",
            secrets_file=Path(temp_dir) / "missing.enc",
            encryption_key=b"0123456789abcdef0123456789abcdef",
            secrets_file_required=False
        )
        
        result = provider.load()
        
        if result != {}:
            errmsg = f"Expected no secrets, got {list(result.keys())}"
            raise AssertionError(errmsg)
    finally:
        shutil.rmtree(temp_dir)
    
    return


# =============================================================================
# The secrets file is authenticated
# =============================================================================

def _encrypt_legacy_secrets(provider: SecretsProvider, secrets_data: Dict[str, str]) -> bytes:
    """
        Encrypt secrets the way releases up to 1.6.0 did: salt + iv +
        AES-256-CBC ciphertext, with no header and no authentication.
        
        :param provider: Provider whose key is used.
        :param secrets_data: The secrets to encrypt.
        
        :returns: The encrypted bytes in the legacy format.
    """
    import json
    
    from cryptography.hazmat.primitives import padding
    from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
    
    salt = os.urandom(16)
    iv = os.urandom(16)
    derived_key = provider._derive_key(provider._encryption_key, salt, iterations=provider.LEGACY_KDF_ITERATIONS)
    
    padder = padding.PKCS7(128).padder()
    padded = padder.update(json.dumps(secrets_data).encode("utf-8")) + padder.finalize()
    
    encryptor = Cipher(algorithms.AES(derived_key), modes.CBC(iv)).encryptor()
    ciphertext = encryptor.update(padded) + encryptor.finalize()
    
    return salt + iv + ciphertext


def test_secrets_provider_encrypted_data_starts_with_versioned_header():
    """
        Test that encrypted secrets start with the format magic and version.
    """
    provider = SecretsProvider(encryption_key=b"0123456789abcdef0123456789abcdef")
    
    encrypted = provider.encrypt_secrets({"api.key": "s3cret"})
    
    expected_header = SecretsProvider.FORMAT_MAGIC + bytes([SecretsProvider.FORMAT_VERSION])
    if not encrypted.startswith(expected_header):
        errmsg = f"Expected the data to start with {expected_header!r}, got {encrypted[:12]!r}"
        raise AssertionError(errmsg)
    
    return


def test_secrets_provider_decrypt_rejects_every_modified_byte():
    """
        Test that changing any single byte of the encrypted data makes
        decryption fail instead of returning altered secrets.
    """
    provider = SecretsProvider(encryption_key=b"0123456789abcdef0123456789abcdef")
    
    encrypted = provider.encrypt_secrets({"a": "secret-value"})
    header_size = len(SecretsProvider.FORMAT_MAGIC) + 1
    
    # One position in each part: header, salt, nonce, ciphertext and tag
    positions = [0, header_size - 1, header_size + 2, header_size + 16 + 2, header_size + 16 + 12 + 2, len(encrypted) - 1]
    
    for position in positions:
        tampered = bytearray(encrypted)
        tampered[position] ^= 0x01
        
        try:
            provider.decrypt_secrets(bytes(tampered))
            errmsg = f"Expected ConfigurationError for a change at byte {position}"
            raise AssertionError(errmsg)
        except ConfigurationError:
            pass  # Expected
    
    return


def test_secrets_provider_decrypt_rejects_wrong_key():
    """
        Test that data encrypted with one key is refused by another.
    """
    writer = SecretsProvider(encryption_key=b"0123456789abcdef0123456789abcdef")
    reader = SecretsProvider(encryption_key=b"fedcba9876543210fedcba9876543210")
    
    encrypted = writer.encrypt_secrets({"a": "secret-value"})
    
    try:
        reader.decrypt_secrets(encrypted)
        errmsg = "Expected ConfigurationError for the wrong key"
        raise AssertionError(errmsg)
    except ConfigurationError:
        pass  # Expected
    
    return


def test_secrets_provider_rejects_legacy_format_by_default():
    """
        Test that data in the unauthenticated legacy format is refused.
    """
    provider = SecretsProvider(encryption_key=b"0123456789abcdef0123456789abcdef")
    
    legacy = _encrypt_legacy_secrets(provider, {"a": "secret-value"})
    
    try:
        provider.decrypt_secrets(legacy)
        errmsg = "Expected ConfigurationError for the legacy format"
        raise AssertionError(errmsg)
    except ConfigurationError as exc:
        if "allow_legacy_secrets_format" not in str(exc):
            errmsg = f"Expected the error to name the opt-in, got {exc}"
            raise AssertionError(errmsg)
    
    return


def test_secrets_provider_reads_legacy_format_when_allowed():
    """
        Test that the legacy format can be read with the explicit opt-in, so
        an old file can be converted.
    """
    import json
    
    provider = SecretsProvider(
        encryption_key=b"0123456789abcdef0123456789abcdef",
        allow_legacy_secrets_format=True
    )
    
    legacy = _encrypt_legacy_secrets(provider, {"a": "secret-value"})
    
    decrypted = provider.decrypt_secrets(legacy)
    
    if json.loads(decrypted) != {"a": "secret-value"}:
        errmsg = f"Expected the legacy secrets to be decrypted, got {decrypted!r}"
        raise AssertionError(errmsg)
    
    return


def test_secrets_provider_rejects_unknown_format_version():
    """
        Test that data with a format version this release does not know is
        refused.
    """
    provider = SecretsProvider(encryption_key=b"0123456789abcdef0123456789abcdef")
    
    encrypted = bytearray(provider.encrypt_secrets({"a": "secret-value"}))
    encrypted[len(SecretsProvider.FORMAT_MAGIC)] = 99
    
    try:
        provider.decrypt_secrets(bytes(encrypted))
        errmsg = "Expected ConfigurationError for an unknown format version"
        raise AssertionError(errmsg)
    except ConfigurationError as exc:
        if "version" not in str(exc):
            errmsg = f"Expected the error to mention the version, got {exc}"
            raise AssertionError(errmsg)
    
    return


# =============================================================================
# Discovery leaves out the files of other environments and profiles
# =============================================================================

def _create_profile_files(directory: str) -> None:
    """
        Create a base settings file and its dev, staging and production
        overlays.
        
        :param directory: Directory to create the files in.
    """
    contents = {
        "settings.json": '{"name": "base", "base_only": 1}',
        "settings.dev.json": '{"name": "dev", "dev_only": 1}',
        "settings.staging.json": '{"name": "staging", "staging_only": 1}',
        "settings.production.json": '{"name": "production"}',
    }
    
    for filename, content in contents.items():
        (Path(directory) / filename).write_text(content)
    
    return


def test_config_file_discovery_leaves_out_other_profiles():
    """
        Test that with profile 'production' the dev and staging overlays are
        not discovered.
    """
    temp_dir = tempfile.mkdtemp()
    
    try:
        _create_profile_files(temp_dir)
        
        discovery = ConfigFileDiscovery(
            appname="testapp",
            search_directories=[temp_dir],
            profile="production"
        )
        
        names = [path.name for path in discovery.discover()]
        
        if names != ["settings.json", "settings.production.json"]:
            errmsg = f"Expected the base file then the production overlay, got {names}"
            raise AssertionError(errmsg)
    finally:
        shutil.rmtree(temp_dir)
    
    return


def test_config_file_discovery_other_profile_keys_do_not_leak():
    """
        Test that keys found only in another profile's file are not loaded.
    """
    temp_dir = tempfile.mkdtemp()
    
    try:
        _create_profile_files(temp_dir)
        
        discovery = ConfigFileDiscovery(
            appname="testapp",
            search_directories=[temp_dir],
            profile="production"
        )
        
        loaded = discovery.create_file_source().load()
        
        expected = {"name": "production", "base_only": 1}
        if loaded != expected:
            errmsg = f"Expected {expected}, got {loaded}"
            raise AssertionError(errmsg)
    finally:
        shutil.rmtree(temp_dir)
    
    return


def test_config_file_discovery_without_profile_finds_base_files_only():
    """
        Test that with no environment and no profile only base files are
        discovered.
    """
    temp_dir = tempfile.mkdtemp()
    
    try:
        _create_profile_files(temp_dir)
        
        discovery = ConfigFileDiscovery(
            appname="testapp",
            search_directories=[temp_dir],
            profile_env_var="WWTEST_UNSET_PROFILE_VAR"
        )
        
        names = [path.name for path in discovery.discover()]
        
        if names != ["settings.json"]:
            errmsg = f"Expected only the base file, got {names}"
            raise AssertionError(errmsg)
    finally:
        shutil.rmtree(temp_dir)
    
    return


def test_config_file_discovery_environment_and_profile_overlays_are_ordered():
    """
        Test that the order is base, then environment overlay, then profile
        overlay.
    """
    temp_dir = tempfile.mkdtemp()
    
    try:
        _create_profile_files(temp_dir)
        
        discovery = ConfigFileDiscovery(
            appname="testapp",
            search_directories=[temp_dir],
            environment="staging",
            profile="dev"
        )
        
        names = [path.name for path in discovery.discover()]
        
        if names != ["settings.json", "settings.staging.json", "settings.dev.json"]:
            errmsg = f"Expected base, environment and profile files in that order, got {names}"
            raise AssertionError(errmsg)
    finally:
        shutil.rmtree(temp_dir)
    
    return


def test_config_file_discovery_orders_base_files_by_name():
    """
        Test that the base files of a directory are returned in name order.
    """
    temp_dir = tempfile.mkdtemp()
    
    try:
        for filename in ("settings.json", "config.json", "testapp.json", "settings.ini"):
            (Path(temp_dir) / filename).write_text("{}" if filename.endswith(".json") else "")
        
        discovery = ConfigFileDiscovery(
            appname="testapp",
            search_directories=[temp_dir],
            profile_env_var="WWTEST_UNSET_PROFILE_VAR"
        )
        
        names = [path.name for path in discovery.discover()]
        
        if names != ["config.json", "settings.ini", "settings.json", "testapp.json"]:
            errmsg = f"Expected the files in name order, got {names}"
            raise AssertionError(errmsg)
    finally:
        shutil.rmtree(temp_dir)
    
    return


def test_config_file_discovery_appname_config_pattern_is_a_base_file():
    """
        Test that '<appname>.config.<ext>' is a base file of the
        '{appname}.config.*' pattern and its profile overlay is found.
    """
    temp_dir = tempfile.mkdtemp()
    
    try:
        for filename in ("testapp.config.json", "testapp.config.production.json", "testapp.config.dev.json"):
            (Path(temp_dir) / filename).write_text("{}")
        
        discovery = ConfigFileDiscovery(
            appname="testapp",
            search_directories=[temp_dir],
            profile="production"
        )
        
        names = [path.name for path in discovery.discover()]
        
        if names != ["testapp.config.json", "testapp.config.production.json"]:
            errmsg = f"Expected the base file and the production overlay, got {names}"
            raise AssertionError(errmsg)
    finally:
        shutil.rmtree(temp_dir)
    
    return
