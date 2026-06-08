"""
    Tests for the extension configuration module.

    This module contains unit tests and property-based tests for
    configuration loading, namespacing, schema validation, defaults
    application, and environment variable overrides.
"""

import os
import random
import string

from typing import Any, Dict, List, Optional

from ccai.webworks.extensibility.configuration import apply_config_defaults
from ccai.webworks.extensibility.configuration import apply_env_overrides
from ccai.webworks.extensibility.configuration import load_extension_config
from ccai.webworks.extensibility.configuration import validate_extension_config
from ccai.webworks.extensibility.exceptions import ExtensionConfigurationError


# =============================================================================
# Random Data Generators for Property Tests
# =============================================================================

def _generate_random_string(min_length: int = 1, max_length: int = 20) -> str:
    """
        Generate a random string of lowercase alphanumeric characters.

        :param min_length: Minimum length of the generated string.
        :param max_length: Maximum length of the generated string.

        :returns: A random alphanumeric string.
    """
    length = random.randint(min_length, max_length)
    result = "".join(random.choices(string.ascii_lowercase + string.digits, k=length))
    return result


def _generate_extension_name() -> str:
    """
        Generate a random extension name using lowercase letters and hyphens.

        :returns: A random extension name string.
    """
    parts_count = random.randint(1, 3)
    parts = []
    for _ in range(parts_count):
        part = "".join(random.choices(string.ascii_lowercase, k=random.randint(3, 8)))
        parts.append(part)

    result = "-".join(parts)
    return result


def _generate_random_config_value(prop_type: str) -> Any:
    """
        Generate a random config value matching the given type.

        :param prop_type: The JSON schema type name.

        :returns: A random value of the specified type.
    """
    if prop_type == "string":
        return _generate_random_string(1, 15)
    elif prop_type == "integer":
        return random.randint(-100, 100)
    elif prop_type == "number":
        return round(random.uniform(-100.0, 100.0), 2)
    elif prop_type == "boolean":
        return random.choice([True, False])
    else:
        return _generate_random_string(1, 10)


# =============================================================================
# Unit Tests for load_extension_config
# =============================================================================

def test_load_config_from_dict_app_config():
    """
        Test loading extension config from a dict-based app config.
    """
    app_config = {
        "extensions": {
            "my_ext": {
                "timeout": 30,
                "debug": True
            }
        }
    }

    result = load_extension_config("my_ext", app_config)

    if result.get("timeout") != 30:
        errmsg = "Expected timeout=30, got {}".format(result.get("timeout"))
        raise AssertionError(errmsg)

    if result.get("debug") is not True:
        errmsg = "Expected debug=True, got {}".format(result.get("debug"))
        raise AssertionError(errmsg)

    return


def test_load_config_returns_empty_when_no_extensions_section():
    """
        Test that an empty dict is returned when no extensions section exists.
    """
    app_config = {"other_key": "value"}

    result = load_extension_config("my_ext", app_config)

    if len(result) != 0:
        errmsg = "Expected empty dict, got {}".format(result)
        raise AssertionError(errmsg)

    return


def test_load_config_returns_empty_when_extension_not_in_config():
    """
        Test that an empty dict is returned when the extension is not configured.
    """
    app_config = {
        "extensions": {
            "other_ext": {"key": "val"}
        }
    }

    result = load_extension_config("my_ext", app_config)

    if len(result) != 0:
        errmsg = "Expected empty dict, got {}".format(result)
        raise AssertionError(errmsg)

    return


def test_load_config_returns_empty_for_non_dict_app_config():
    """
        Test that an empty dict is returned when app_config is not a dict.
    """
    result = load_extension_config("my_ext", None)

    if len(result) != 0:
        errmsg = "Expected empty dict, got {}".format(result)
        raise AssertionError(errmsg)

    return


def test_load_config_returns_copy_not_reference():
    """
        Test that load_extension_config returns a copy, not a reference.
    """
    inner = {"key": "val"}
    app_config = {"extensions": {"my_ext": inner}}

    result = load_extension_config("my_ext", app_config)

    if result is inner:
        errmsg = "Expected a copy of the config, not the same reference"
        raise AssertionError(errmsg)

    return


# =============================================================================
# Property-Based Test: Property 22 - Extension Configuration Namespacing
# =============================================================================

def test_property_22_extension_configuration_namespacing():
    """
        Property 22: Extension Configuration Namespacing

        For any extension with configuration, the configuration keys
        SHALL be namespaced by extension name (e.g.,
        extensions.my_extension.setting). Loading config for extension
        X from an app config with extensions.X.key SHALL return that
        key, and loading config for extension Y SHALL NOT return
        extension X's config.

        **Validates: Requirements 9.1, 9.2, 9.3**
    """
    for iteration in range(100):
        # Generate two distinct extension names
        ext_name_a = _generate_extension_name()
        ext_name_b = ext_name_a + "_other"

        # Generate random config for extension A
        config_a = {}
        key_count = random.randint(1, 5)
        for _ in range(key_count):
            key = _generate_random_string(3, 10)
            value = _generate_random_string(1, 15)
            config_a[key] = value

        # Build app config with namespaced extension config
        app_config = {
            "extensions": {
                ext_name_a: dict(config_a)
            }
        }

        # Loading config for ext_name_a should return its config
        result_a = load_extension_config(ext_name_a, app_config)

        for key, expected_value in config_a.items():
            actual_value = result_a.get(key)
            if actual_value != expected_value:
                errmsg = (
                    "Iteration {}: Expected config key '{}' = '{}' for extension '{}', "
                    "got '{}'"
                ).format(iteration, key, expected_value, ext_name_a, actual_value)
                raise AssertionError(errmsg)

        # Loading config for ext_name_b should return empty dict
        result_b = load_extension_config(ext_name_b, app_config)

        if len(result_b) != 0:
            errmsg = (
                "Iteration {}: Expected empty config for extension '{}', got {}"
            ).format(iteration, ext_name_b, result_b)
            raise AssertionError(errmsg)

    return


# =============================================================================
# Unit Tests for validate_extension_config
# =============================================================================

def test_validate_config_passes_with_no_schema():
    """
        Test that validation passes when no schema is provided.
    """
    validate_extension_config("my_ext", {"key": "val"}, None)
    return


def test_validate_config_passes_with_valid_config():
    """
        Test that validation passes when config matches schema.
    """
    schema = {
        "properties": {
            "timeout": {"type": "integer"},
            "name": {"type": "string"}
        },
        "required": ["timeout"]
    }
    config = {"timeout": 30, "name": "test"}

    validate_extension_config("my_ext", config, schema)
    return


def test_validate_config_raises_on_missing_required_key():
    """
        Test that validation raises ExtensionConfigurationError
        when a required key is missing.
    """
    schema = {
        "properties": {
            "timeout": {"type": "integer"}
        },
        "required": ["timeout"]
    }
    config = {}

    raised = False
    caught_error = None
    try:
        validate_extension_config("my_ext", config, schema)
    except ExtensionConfigurationError as err:
        raised = True
        caught_error = err

    if raised is not True:
        errmsg = "Expected ExtensionConfigurationError for missing required key"
        raise AssertionError(errmsg)

    if caught_error.extension_name != "my_ext":
        errmsg = "Expected extension_name 'my_ext', got '{}'".format(caught_error.extension_name)
        raise AssertionError(errmsg)

    if caught_error.key != "timeout":
        errmsg = "Expected key 'timeout', got '{}'".format(caught_error.key)
        raise AssertionError(errmsg)

    return


def test_validate_config_raises_on_wrong_type():
    """
        Test that validation raises ExtensionConfigurationError
        when a value has the wrong type.
    """
    schema = {
        "properties": {
            "timeout": {"type": "integer"}
        }
    }
    config = {"timeout": "not_an_int"}

    raised = False
    try:
        validate_extension_config("my_ext", config, schema)
    except ExtensionConfigurationError:
        raised = True

    if raised is not True:
        errmsg = "Expected ExtensionConfigurationError for wrong type"
        raise AssertionError(errmsg)

    return


def test_validate_config_allows_extra_keys_not_in_schema():
    """
        Test that validation allows keys not defined in the schema.
    """
    schema = {
        "properties": {
            "timeout": {"type": "integer"}
        }
    }
    config = {"timeout": 30, "extra_key": "extra_value"}

    validate_extension_config("my_ext", config, schema)
    return


# =============================================================================
# Property-Based Test: Property 23 - Extension Configuration Validation
# =============================================================================

def test_property_23_extension_configuration_validation():
    """
        Property 23: Extension Configuration Validation

        For any extension with a configuration schema, loading the
        extension SHALL validate its configuration against the schema
        and raise ExtensionConfigurationError if validation fails.

        Specifically:
        - Config with all required keys and correct types SHALL pass.
        - Config missing a required key SHALL raise ExtensionConfigurationError.
        - Config with a wrong type for a defined property SHALL raise
          ExtensionConfigurationError.

        **Validates: Requirements 9.5, 9.6**
    """
    type_choices = ["string", "integer", "number", "boolean"]

    for iteration in range(100):
        ext_name = _generate_extension_name()

        # Generate a random schema with 1-4 properties
        prop_count = random.randint(1, 4)
        properties = {}
        prop_names = []

        for _ in range(prop_count):
            pname = _generate_random_string(3, 10)
            ptype = random.choice(type_choices)
            properties[pname] = {"type": ptype}
            prop_names.append(pname)

        # Pick a random subset as required
        required_count = random.randint(1, len(prop_names))
        required_keys = random.sample(prop_names, required_count)

        schema = {
            "properties": properties,
            "required": required_keys
        }

        # Case 1: Valid config with all required keys and correct types
        valid_config = {}
        for pname in prop_names:
            ptype = properties[pname]["type"]
            valid_config[pname] = _generate_random_config_value(ptype)

        # Should not raise
        validate_extension_config(ext_name, valid_config, schema)

        # Case 2: Missing a required key should raise
        if len(required_keys) > 0:
            missing_key = random.choice(required_keys)
            incomplete_config = dict(valid_config)
            del incomplete_config[missing_key]

            raised = False
            caught_error = None
            try:
                validate_extension_config(ext_name, incomplete_config, schema)
            except ExtensionConfigurationError as err:
                raised = True
                caught_error = err

            if raised is not True:
                errmsg = (
                    "Iteration {}: Expected ExtensionConfigurationError for "
                    "missing required key '{}'"
                ).format(iteration, missing_key)
                raise AssertionError(errmsg)

            if caught_error.extension_name != ext_name:
                errmsg = (
                    "Iteration {}: Expected extension_name '{}', got '{}'"
                ).format(iteration, ext_name, caught_error.extension_name)
                raise AssertionError(errmsg)

        # Case 3: Wrong type should raise
        # Pick a property and give it a value of the wrong type
        target_prop = random.choice(prop_names)
        target_type = properties[target_prop]["type"]

        # Generate a value of a different type
        wrong_type_map = {
            "string": "integer",
            "integer": "string",
            "number": "string",
            "boolean": "string",
        }
        wrong_type = wrong_type_map.get(target_type, "integer")
        wrong_value = _generate_random_config_value(wrong_type)

        wrong_config = dict(valid_config)
        wrong_config[target_prop] = wrong_value

        raised = False
        try:
            validate_extension_config(ext_name, wrong_config, schema)
        except ExtensionConfigurationError:
            raised = True

        if raised is not True:
            errmsg = (
                "Iteration {}: Expected ExtensionConfigurationError for "
                "wrong type on key '{}' (expected '{}', gave '{}')"
            ).format(iteration, target_prop, target_type, type(wrong_value).__name__)
            raise AssertionError(errmsg)

    return


# =============================================================================
# Unit Tests for apply_config_defaults
# =============================================================================

def test_apply_defaults_fills_missing_keys():
    """
        Test that apply_config_defaults fills in missing keys with defaults.
    """
    schema = {
        "properties": {
            "timeout": {"type": "integer", "default": 60},
            "debug": {"type": "boolean", "default": False}
        }
    }
    config = {}

    result = apply_config_defaults(config, schema)

    if result.get("timeout") != 60:
        errmsg = "Expected timeout=60, got {}".format(result.get("timeout"))
        raise AssertionError(errmsg)

    if result.get("debug") is not False:
        errmsg = "Expected debug=False, got {}".format(result.get("debug"))
        raise AssertionError(errmsg)

    return


def test_apply_defaults_does_not_overwrite_existing_keys():
    """
        Test that apply_config_defaults does not overwrite existing values.
    """
    schema = {
        "properties": {
            "timeout": {"type": "integer", "default": 60}
        }
    }
    config = {"timeout": 120}

    result = apply_config_defaults(config, schema)

    if result.get("timeout") != 120:
        errmsg = "Expected timeout=120 (not overwritten), got {}".format(result.get("timeout"))
        raise AssertionError(errmsg)

    return


def test_apply_defaults_returns_copy():
    """
        Test that apply_config_defaults returns a new dict, not the original.
    """
    config = {"key": "val"}
    result = apply_config_defaults(config, None)

    if result is config:
        errmsg = "Expected a new dict, not the same reference"
        raise AssertionError(errmsg)

    return


def test_apply_defaults_with_no_schema():
    """
        Test that apply_config_defaults returns config unchanged when no schema.
    """
    config = {"key": "val"}
    result = apply_config_defaults(config, None)

    if result != config:
        errmsg = "Expected config unchanged, got {}".format(result)
        raise AssertionError(errmsg)

    return


# =============================================================================
# Property-Based Test: Property 24 - Extension Configuration Defaults
# =============================================================================

def test_property_24_extension_configuration_defaults():
    """
        Property 24: Extension Configuration Defaults

        For any extension configuration key with a default value in
        the schema, if the key is not provided in the config, the
        default value SHALL be used. If the key IS provided, the
        provided value SHALL be preserved.

        **Validates: Requirements 9.7**
    """
    type_choices = ["string", "integer", "number", "boolean"]

    for iteration in range(100):
        # Generate a random schema with defaults
        prop_count = random.randint(1, 5)
        properties = {}
        prop_names = []
        defaults = {}

        for _ in range(prop_count):
            pname = _generate_random_string(3, 10)
            ptype = random.choice(type_choices)
            default_val = _generate_random_config_value(ptype)
            properties[pname] = {"type": ptype, "default": default_val}
            prop_names.append(pname)
            defaults[pname] = default_val

        schema = {"properties": properties}

        # Randomly decide which keys to provide vs leave for defaults
        provided_count = random.randint(0, len(prop_names))
        provided_keys = random.sample(prop_names, provided_count)

        config = {}
        for pname in provided_keys:
            ptype = properties[pname]["type"]
            config[pname] = _generate_random_config_value(ptype)

        result = apply_config_defaults(config, schema)

        # Verify: provided keys keep their values
        for pname in provided_keys:
            if result[pname] != config[pname]:
                errmsg = (
                    "Iteration {}: Provided key '{}' should keep value '{}', "
                    "got '{}'"
                ).format(iteration, pname, config[pname], result[pname])
                raise AssertionError(errmsg)

        # Verify: missing keys get their defaults
        missing_keys = [p for p in prop_names if p not in provided_keys]
        for pname in missing_keys:
            expected_default = defaults[pname]
            if result.get(pname) != expected_default:
                errmsg = (
                    "Iteration {}: Missing key '{}' should get default '{}', "
                    "got '{}'"
                ).format(iteration, pname, expected_default, result.get(pname))
                raise AssertionError(errmsg)

    return


# =============================================================================
# Unit Tests for apply_env_overrides
# =============================================================================

def test_env_override_applies_string_value():
    """
        Test that environment variable overrides apply string values.
    """
    schema = {
        "properties": {
            "host": {"type": "string"}
        }
    }
    config = {"host": "localhost"}

    env_var = "EXTENSION_MY_EXT_HOST"
    original_value = os.environ.get(env_var, None)

    try:
        os.environ[env_var] = "remote-host"
        result = apply_env_overrides("my_ext", config, schema)

        if result.get("host") != "remote-host":
            errmsg = "Expected host='remote-host', got '{}'".format(result.get("host"))
            raise AssertionError(errmsg)
    finally:
        if original_value is None:
            os.environ.pop(env_var, None)
        else:
            os.environ[env_var] = original_value

    return


def test_env_override_coerces_integer():
    """
        Test that environment variable overrides coerce integer values.
    """
    schema = {
        "properties": {
            "port": {"type": "integer"}
        }
    }
    config = {"port": 8080}

    env_var = "EXTENSION_MY_EXT_PORT"
    original_value = os.environ.get(env_var, None)

    try:
        os.environ[env_var] = "9090"
        result = apply_env_overrides("my_ext", config, schema)

        if result.get("port") != 9090:
            errmsg = "Expected port=9090, got {}".format(result.get("port"))
            raise AssertionError(errmsg)

        if not isinstance(result.get("port"), int):
            errmsg = "Expected port to be int, got {}".format(type(result.get("port")))
            raise AssertionError(errmsg)
    finally:
        if original_value is None:
            os.environ.pop(env_var, None)
        else:
            os.environ[env_var] = original_value

    return


def test_env_override_coerces_boolean():
    """
        Test that environment variable overrides coerce boolean values.
    """
    schema = {
        "properties": {
            "debug": {"type": "boolean"}
        }
    }
    config = {"debug": False}

    env_var = "EXTENSION_MY_EXT_DEBUG"
    original_value = os.environ.get(env_var, None)

    try:
        os.environ[env_var] = "true"
        result = apply_env_overrides("my_ext", config, schema)

        if result.get("debug") is not True:
            errmsg = "Expected debug=True, got {}".format(result.get("debug"))
            raise AssertionError(errmsg)
    finally:
        if original_value is None:
            os.environ.pop(env_var, None)
        else:
            os.environ[env_var] = original_value

    return


def test_env_override_does_not_apply_without_env_var():
    """
        Test that config is unchanged when no env var is set.
    """
    schema = {
        "properties": {
            "host": {"type": "string"}
        }
    }
    config = {"host": "localhost"}

    # Ensure the env var is not set
    env_var = "EXTENSION_MY_EXT_HOST"
    original_value = os.environ.get(env_var, None)

    try:
        os.environ.pop(env_var, None)
        result = apply_env_overrides("my_ext", config, schema)

        if result.get("host") != "localhost":
            errmsg = "Expected host='localhost', got '{}'".format(result.get("host"))
            raise AssertionError(errmsg)
    finally:
        if original_value is not None:
            os.environ[env_var] = original_value

    return


def test_env_override_with_no_schema():
    """
        Test that apply_env_overrides returns config unchanged when no schema.
    """
    config = {"key": "val"}
    result = apply_env_overrides("my_ext", config, None)

    if result != config:
        errmsg = "Expected config unchanged, got {}".format(result)
        raise AssertionError(errmsg)

    return


def test_env_override_hyphenated_extension_name():
    """
        Test that hyphens in extension names are converted to underscores
        in the environment variable name.
    """
    schema = {
        "properties": {
            "timeout": {"type": "integer"}
        }
    }
    config = {"timeout": 30}

    env_var = "EXTENSION_MY_COOL_EXT_TIMEOUT"
    original_value = os.environ.get(env_var, None)

    try:
        os.environ[env_var] = "99"
        result = apply_env_overrides("my-cool-ext", config, schema)

        if result.get("timeout") != 99:
            errmsg = "Expected timeout=99, got {}".format(result.get("timeout"))
            raise AssertionError(errmsg)
    finally:
        if original_value is None:
            os.environ.pop(env_var, None)
        else:
            os.environ[env_var] = original_value

    return
