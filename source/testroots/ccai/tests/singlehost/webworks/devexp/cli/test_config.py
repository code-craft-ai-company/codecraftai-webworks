"""
    Tests for the webworks CLI configuration loading module.

    This module contains unit tests for loading configuration from
    default values, JSON files, and environment variables. It verifies
    that the merge precedence is correct: environment variables override
    file config, which overrides defaults.
"""

import json
import os
import tempfile

from ccai.webworks.devexp.cli.config import (
    DEFAULT_CONFIG,
    ENV_PREFIX,
    load_config,
    load_config_from_env,
    load_config_from_file,
    merge_configs,
)


# =============================================================================
# Unit Tests for Default Configuration
# =============================================================================

def test_default_config_has_server_section():
    """
        Test that the default configuration contains a server section.
    """
    if "server" not in DEFAULT_CONFIG:
        errmsg = "Expected 'server' section in DEFAULT_CONFIG"
        raise AssertionError(errmsg)

    return


def test_default_config_server_host():
    """
        Test that the default server host is 127.0.0.1.
    """
    host = DEFAULT_CONFIG["server"]["host"]

    if host != "127.0.0.1":
        errmsg = "Expected default server host '127.0.0.1', got '{}'".format(host)
        raise AssertionError(errmsg)

    return


def test_default_config_server_port():
    """
        Test that the default server port is 8000.
    """
    port = DEFAULT_CONFIG["server"]["port"]

    if port != 8000:
        errmsg = "Expected default server port 8000, got {}".format(port)
        raise AssertionError(errmsg)

    return


def test_default_config_has_logging_section():
    """
        Test that the default configuration contains a logging section.
    """
    if "logging" not in DEFAULT_CONFIG:
        errmsg = "Expected 'logging' section in DEFAULT_CONFIG"
        raise AssertionError(errmsg)

    return


def test_default_config_has_debug_section():
    """
        Test that the default configuration contains a debug section.
    """
    if "debug" not in DEFAULT_CONFIG:
        errmsg = "Expected 'debug' section in DEFAULT_CONFIG"
        raise AssertionError(errmsg)

    return


def test_default_config_has_inspector_section():
    """
        Test that the default configuration contains an inspector section.
    """
    if "inspector" not in DEFAULT_CONFIG:
        errmsg = "Expected 'inspector' section in DEFAULT_CONFIG"
        raise AssertionError(errmsg)

    return


# =============================================================================
# Unit Tests for load_config_from_file
# =============================================================================

def test_load_config_from_file_returns_empty_for_missing_file():
    """
        Test that loading from a nonexistent file returns an empty dict.
    """
    result = load_config_from_file("/nonexistent/path/config.json")

    if len(result) != 0:
        errmsg = "Expected empty dict for missing file, got {} entries".format(len(result))
        raise AssertionError(errmsg)

    return


def test_load_config_from_file_reads_json():
    """
        Test that a valid JSON config file is loaded correctly.
    """
    config_data = {"server": {"host": "0.0.0.0", "port": 9000}}

    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as tmp:
        json.dump(config_data, tmp)
        tmp_path = tmp.name

    try:
        result = load_config_from_file(tmp_path)

        if result.get("server", {}).get("host") != "0.0.0.0":
            errmsg = "Expected host '0.0.0.0', got '{}'".format(
                result.get("server", {}).get("host")
            )
            raise AssertionError(errmsg)

        if result.get("server", {}).get("port") != 9000:
            errmsg = "Expected port 9000, got {}".format(
                result.get("server", {}).get("port")
            )
            raise AssertionError(errmsg)
    finally:
        os.unlink(tmp_path)

    return


def test_load_config_from_file_returns_empty_for_invalid_json():
    """
        Test that an invalid JSON file returns an empty dict.
    """
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as tmp:
        tmp.write("not valid json {{{")
        tmp_path = tmp.name

    try:
        result = load_config_from_file(tmp_path)

        if len(result) != 0:
            errmsg = "Expected empty dict for invalid JSON, got {} entries".format(len(result))
            raise AssertionError(errmsg)
    finally:
        os.unlink(tmp_path)

    return


def test_load_config_from_file_returns_empty_for_non_dict_json():
    """
        Test that a JSON file containing a non-dict value returns empty dict.
    """
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as tmp:
        json.dump([1, 2, 3], tmp)
        tmp_path = tmp.name

    try:
        result = load_config_from_file(tmp_path)

        if len(result) != 0:
            errmsg = "Expected empty dict for non-dict JSON, got {} entries".format(len(result))
            raise AssertionError(errmsg)
    finally:
        os.unlink(tmp_path)

    return


# =============================================================================
# Unit Tests for load_config_from_env
# =============================================================================

def test_load_config_from_env_reads_string_value():
    """
        Test that a WEBWORKS_ environment variable is read as a config value.
    """
    env_key = "WEBWORKS_SERVER_HOST"
    original = os.environ.get(env_key)

    try:
        os.environ[env_key] = "0.0.0.0"
        result = load_config_from_env()

        host = result.get("server", {}).get("host")
        if host != "0.0.0.0":
            errmsg = "Expected host '0.0.0.0', got '{}'".format(host)
            raise AssertionError(errmsg)
    finally:
        if original is None:
            os.environ.pop(env_key, None)
        else:
            os.environ[env_key] = original

    return


def test_load_config_from_env_coerces_int_value():
    """
        Test that an integer environment variable is coerced to int.
    """
    env_key = "WEBWORKS_SERVER_PORT"
    original = os.environ.get(env_key)

    try:
        os.environ[env_key] = "9090"
        result = load_config_from_env()

        port = result.get("server", {}).get("port")
        if port != 9090:
            errmsg = "Expected port 9090 (int), got {} ({})".format(port, type(port).__name__)
            raise AssertionError(errmsg)
    finally:
        if original is None:
            os.environ.pop(env_key, None)
        else:
            os.environ[env_key] = original

    return


def test_load_config_from_env_coerces_bool_true():
    """
        Test that a boolean environment variable 'true' is coerced to True.
    """
    env_key = "WEBWORKS_SERVER_DEBUG"
    original = os.environ.get(env_key)

    try:
        os.environ[env_key] = "true"
        result = load_config_from_env()

        debug = result.get("server", {}).get("debug")
        if debug is not True:
            errmsg = "Expected debug True, got {} ({})".format(debug, type(debug).__name__)
            raise AssertionError(errmsg)
    finally:
        if original is None:
            os.environ.pop(env_key, None)
        else:
            os.environ[env_key] = original

    return


def test_load_config_from_env_coerces_bool_false():
    """
        Test that a boolean environment variable 'false' is coerced to False.
    """
    env_key = "WEBWORKS_SERVER_RELOAD"
    original = os.environ.get(env_key)

    try:
        os.environ[env_key] = "false"
        result = load_config_from_env()

        reload_val = result.get("server", {}).get("reload")
        if reload_val is not False:
            errmsg = "Expected reload False, got {} ({})".format(reload_val, type(reload_val).__name__)
            raise AssertionError(errmsg)
    finally:
        if original is None:
            os.environ.pop(env_key, None)
        else:
            os.environ[env_key] = original

    return


def test_load_config_from_env_coerces_none_value():
    """
        Test that the string 'none' is coerced to None for keys with None default.
    """
    env_key = "WEBWORKS_DEBUG_PIN"
    original = os.environ.get(env_key)

    try:
        os.environ[env_key] = "none"
        result = load_config_from_env()

        pin = result.get("debug", {}).get("pin")
        if pin is not None:
            errmsg = "Expected pin None, got {} ({})".format(pin, type(pin).__name__)
            raise AssertionError(errmsg)
    finally:
        if original is None:
            os.environ.pop(env_key, None)
        else:
            os.environ[env_key] = original

    return


def test_load_config_from_env_ignores_non_prefixed_vars():
    """
        Test that environment variables without the WEBWORKS_ prefix are ignored.
    """
    env_key = "SOME_OTHER_VAR"
    original = os.environ.get(env_key)

    try:
        os.environ[env_key] = "should_be_ignored"
        result = load_config_from_env()

        if "some" in result:
            errmsg = "Non-prefixed variable should not appear in config"
            raise AssertionError(errmsg)
    finally:
        if original is None:
            os.environ.pop(env_key, None)
        else:
            os.environ[env_key] = original

    return


def test_load_config_from_env_ignores_single_part_suffix():
    """
        Test that a WEBWORKS_ variable with only one part after the prefix
        is ignored (requires section_key format).
    """
    env_key = "WEBWORKS_STANDALONE"
    original = os.environ.get(env_key)

    try:
        os.environ[env_key] = "value"
        result = load_config_from_env()

        if "standalone" in result:
            errmsg = "Single-part suffix should not create a config entry"
            raise AssertionError(errmsg)
    finally:
        if original is None:
            os.environ.pop(env_key, None)
        else:
            os.environ[env_key] = original

    return


# =============================================================================
# Unit Tests for merge_configs
# =============================================================================

def test_merge_configs_override_replaces_value():
    """
        Test that override values replace base values.
    """
    base = {"server": {"host": "127.0.0.1", "port": 8000}}
    override = {"server": {"host": "0.0.0.0"}}

    result = merge_configs(base, override)

    if result["server"]["host"] != "0.0.0.0":
        errmsg = "Expected host '0.0.0.0', got '{}'".format(result["server"]["host"])
        raise AssertionError(errmsg)

    return


def test_merge_configs_preserves_non_overridden_values():
    """
        Test that values not in the override are preserved from the base.
    """
    base = {"server": {"host": "127.0.0.1", "port": 8000}}
    override = {"server": {"host": "0.0.0.0"}}

    result = merge_configs(base, override)

    if result["server"]["port"] != 8000:
        errmsg = "Expected port 8000, got {}".format(result["server"]["port"])
        raise AssertionError(errmsg)

    return


def test_merge_configs_adds_new_sections():
    """
        Test that new sections from the override are added.
    """
    base = {"server": {"host": "127.0.0.1"}}
    override = {"custom": {"key": "value"}}

    result = merge_configs(base, override)

    if "custom" not in result:
        errmsg = "Expected 'custom' section in merged config"
        raise AssertionError(errmsg)

    if result["custom"]["key"] != "value":
        errmsg = "Expected custom.key 'value', got '{}'".format(result["custom"]["key"])
        raise AssertionError(errmsg)

    return


def test_merge_configs_does_not_mutate_base():
    """
        Test that the base dictionary is not modified by the merge.
    """
    base = {"server": {"host": "127.0.0.1"}}
    override = {"server": {"host": "0.0.0.0"}}

    merge_configs(base, override)

    if base["server"]["host"] != "127.0.0.1":
        errmsg = "Base dict was mutated: host is now '{}'".format(base["server"]["host"])
        raise AssertionError(errmsg)

    return


# =============================================================================
# Unit Tests for load_config (full integration)
# =============================================================================

def test_load_config_returns_defaults_with_no_file_or_env():
    """
        Test that load_config returns default values when no file or
        environment variables are provided.
    """
    # Clean any WEBWORKS_ env vars that might interfere
    saved_env = {}
    for key in list(os.environ.keys()):
        if key.startswith(ENV_PREFIX):
            saved_env[key] = os.environ.pop(key)

    try:
        result = load_config()

        if result["server"]["host"] != "127.0.0.1":
            errmsg = "Expected default host '127.0.0.1', got '{}'".format(
                result["server"]["host"]
            )
            raise AssertionError(errmsg)

        if result["server"]["port"] != 8000:
            errmsg = "Expected default port 8000, got {}".format(result["server"]["port"])
            raise AssertionError(errmsg)
    finally:
        os.environ.update(saved_env)

    return


def test_load_config_file_overrides_defaults():
    """
        Test that file configuration overrides default values.
    """
    saved_env = {}
    for key in list(os.environ.keys()):
        if key.startswith(ENV_PREFIX):
            saved_env[key] = os.environ.pop(key)

    config_data = {"server": {"host": "192.168.1.1"}}

    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as tmp:
        json.dump(config_data, tmp)
        tmp_path = tmp.name

    try:
        result = load_config(config_path=tmp_path)

        if result["server"]["host"] != "192.168.1.1":
            errmsg = "Expected host '192.168.1.1', got '{}'".format(
                result["server"]["host"]
            )
            raise AssertionError(errmsg)

        # Non-overridden defaults should still be present
        if result["server"]["port"] != 8000:
            errmsg = "Expected default port 8000, got {}".format(result["server"]["port"])
            raise AssertionError(errmsg)
    finally:
        os.unlink(tmp_path)
        os.environ.update(saved_env)

    return


def test_load_config_env_overrides_file():
    """
        Test that environment variables take precedence over file config.
    """
    saved_env = {}
    for key in list(os.environ.keys()):
        if key.startswith(ENV_PREFIX):
            saved_env[key] = os.environ.pop(key)

    config_data = {"server": {"host": "192.168.1.1", "port": 9000}}

    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as tmp:
        json.dump(config_data, tmp)
        tmp_path = tmp.name

    try:
        os.environ["WEBWORKS_SERVER_HOST"] = "10.0.0.1"

        result = load_config(config_path=tmp_path)

        # Env var should override the file value
        if result["server"]["host"] != "10.0.0.1":
            errmsg = "Expected env override host '10.0.0.1', got '{}'".format(
                result["server"]["host"]
            )
            raise AssertionError(errmsg)

        # File value should override default for non-env keys
        if result["server"]["port"] != 9000:
            errmsg = "Expected file port 9000, got {}".format(result["server"]["port"])
            raise AssertionError(errmsg)
    finally:
        os.environ.pop("WEBWORKS_SERVER_HOST", None)
        os.unlink(tmp_path)
        os.environ.update(saved_env)

    return


def test_load_config_env_overrides_defaults():
    """
        Test that environment variables override default values even
        without a config file.
    """
    saved_env = {}
    for key in list(os.environ.keys()):
        if key.startswith(ENV_PREFIX):
            saved_env[key] = os.environ.pop(key)

    try:
        os.environ["WEBWORKS_SERVER_PORT"] = "3000"

        result = load_config()

        if result["server"]["port"] != 3000:
            errmsg = "Expected env override port 3000, got {}".format(
                result["server"]["port"]
            )
            raise AssertionError(errmsg)
    finally:
        os.environ.pop("WEBWORKS_SERVER_PORT", None)
        os.environ.update(saved_env)

    return


def test_load_config_missing_file_uses_defaults():
    """
        Test that a missing config file path falls back to defaults.
    """
    saved_env = {}
    for key in list(os.environ.keys()):
        if key.startswith(ENV_PREFIX):
            saved_env[key] = os.environ.pop(key)

    try:
        result = load_config(config_path="/nonexistent/config.json")

        if result["server"]["host"] != "127.0.0.1":
            errmsg = "Expected default host '127.0.0.1', got '{}'".format(
                result["server"]["host"]
            )
            raise AssertionError(errmsg)
    finally:
        os.environ.update(saved_env)

    return


def test_load_config_pin_set_from_env():
    """
        Test that a non-none string value for a None-default key is
        preserved from the environment.
    """
    saved_env = {}
    for key in list(os.environ.keys()):
        if key.startswith(ENV_PREFIX):
            saved_env[key] = os.environ.pop(key)

    try:
        os.environ["WEBWORKS_DEBUG_PIN"] = "12345"

        result = load_config()

        pin = result["debug"]["pin"]
        if pin != "12345":
            errmsg = "Expected pin '12345', got '{}'".format(pin)
            raise AssertionError(errmsg)
    finally:
        os.environ.pop("WEBWORKS_DEBUG_PIN", None)
        os.environ.update(saved_env)

    return

# =============================================================================
# Property Tests for Configuration Precedence
# Validates: Requirements 1.5, 1.6
# =============================================================================

import random
import string


# ---------------------------------------------------------------------------
# Helpers for generating random configuration values
# ---------------------------------------------------------------------------

def _random_string(min_length=3, max_length=20):
    """
        Generate a random alphanumeric string.
    """
    length = random.randint(min_length, max_length)
    return "".join(random.choices(string.ascii_lowercase + string.digits, k=length))


def _random_host():
    """
        Generate a random IPv4 address string.
    """
    return "{}.{}.{}.{}".format(
        random.randint(0, 255),
        random.randint(0, 255),
        random.randint(0, 255),
        random.randint(0, 255),
    )


def _random_port():
    """
        Generate a random port number.
    """
    return random.randint(1024, 65535)


def _random_bool():
    """
        Generate a random boolean.
    """
    return random.choice([True, False])


def _random_int(low=1, high=100000):
    """
        Generate a random integer in the given range.
    """
    return random.randint(low, high)


def _random_log_level():
    """
        Generate a random log level string.
    """
    return random.choice(["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"])


# A list of testable config keys with their section, key, random value
# generator, and the environment variable format.
_CONFIG_KEYS = [
    ("server", "host", _random_host, str),
    ("server", "port", _random_port, int),
    ("server", "debug", _random_bool, bool),
    ("server", "reload", _random_bool, bool),
    ("logging", "level", _random_log_level, str),
    ("logging", "colors", _random_bool, bool),
    ("debug", "interactive", _random_bool, bool),
    ("debug", "timeout", lambda: _random_int(10, 3600), int),
    ("inspector", "enabled", _random_bool, bool),
    ("inspector", "max_requests", lambda: _random_int(1, 1000), int),
    ("inspector", "max_body_size", lambda: _random_int(512, 1048576), int),
]


def _env_key_for(section, key):
    """
        Build the environment variable name for a config section and key.
    """
    return "{}{}_{}" .format(ENV_PREFIX, section.upper(), key.upper())


def _env_str_for(value, value_type):
    """
        Convert a Python value to the string representation used in
        environment variables.
    """
    if value_type is bool:
        return "true" if value else "false"
    return str(value)


def _pick_random_keys(count=None):
    """
        Pick a random subset of config keys for a single iteration.
    """
    if count is None:
        count = random.randint(1, len(_CONFIG_KEYS))
    return random.sample(_CONFIG_KEYS, k=count)


def _save_and_clear_webworks_env():
    """
        Save and remove all WEBWORKS_ environment variables so they do
        not interfere with the test iteration.

        :returns: A dictionary of saved environment variables.
    """
    saved = {}
    for env_name in list(os.environ.keys()):
        if env_name.startswith(ENV_PREFIX):
            saved[env_name] = os.environ.pop(env_name)
    return saved


def _restore_env(saved):
    """
        Restore previously saved environment variables and remove any
        WEBWORKS_ variables that were set during the test iteration.
    """
    for env_name in list(os.environ.keys()):
        if env_name.startswith(ENV_PREFIX):
            os.environ.pop(env_name, None)
    os.environ.update(saved)


# ---------------------------------------------------------------------------
# Property 8: Configuration Precedence
# ---------------------------------------------------------------------------

_NUM_ITERATIONS = 100


def test_property_env_overrides_file_config():
    """
        **Validates: Requirements 1.5, 1.6**

        Property: For any configuration key, when both a file config
        value and an environment variable are present, the environment
        variable value SHALL take precedence.

        This test generates random values for a random subset of config
        keys, writes one set to a JSON file and sets a different set as
        environment variables, then verifies the env values win.
    """
    for iteration in range(_NUM_ITERATIONS):
        saved_env = _save_and_clear_webworks_env()
        tmp_path = None

        try:
            keys = _pick_random_keys()

            file_config = {}
            env_values = {}

            for section, key, gen_fn, val_type in keys:
                file_val = gen_fn()
                env_val = gen_fn()

                # Ensure the two values differ so the test is meaningful
                while env_val == file_val:
                    env_val = gen_fn()

                if section not in file_config:
                    file_config[section] = {}
                file_config[section][key] = file_val

                env_name = _env_key_for(section, key)
                os.environ[env_name] = _env_str_for(env_val, val_type)
                env_values[(section, key)] = env_val

            with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as tmp:
                json.dump(file_config, tmp)
                tmp_path = tmp.name

            result = load_config(config_path=tmp_path)

            for (section, key), expected in env_values.items():
                actual = result[section][key]
                if actual != expected:
                    errmsg = (
                        "Iteration {}: env should override file for {}.{}. "
                        "Expected {!r}, got {!r}"
                    ).format(iteration, section, key, expected, actual)
                    raise AssertionError(errmsg)

        finally:
            if tmp_path is not None:
                os.unlink(tmp_path)
            _restore_env(saved_env)

    return


def test_property_file_overrides_defaults():
    """
        **Validates: Requirements 1.5, 1.6**

        Property: For any configuration key, when a file config value
        is present and no environment variable is set, the file value
        SHALL take precedence over the default value.
    """
    for iteration in range(_NUM_ITERATIONS):
        saved_env = _save_and_clear_webworks_env()
        tmp_path = None

        try:
            keys = _pick_random_keys()

            file_config = {}
            expected_values = {}

            for section, key, gen_fn, val_type in keys:
                file_val = gen_fn()
                default_val = DEFAULT_CONFIG.get(section, {}).get(key)

                # Ensure the file value differs from the default
                while file_val == default_val:
                    file_val = gen_fn()

                if section not in file_config:
                    file_config[section] = {}
                file_config[section][key] = file_val
                expected_values[(section, key)] = file_val

            with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as tmp:
                json.dump(file_config, tmp)
                tmp_path = tmp.name

            result = load_config(config_path=tmp_path)

            for (section, key), expected in expected_values.items():
                actual = result[section][key]
                if actual != expected:
                    errmsg = (
                        "Iteration {}: file should override default for {}.{}. "
                        "Expected {!r}, got {!r}"
                    ).format(iteration, section, key, expected, actual)
                    raise AssertionError(errmsg)

        finally:
            if tmp_path is not None:
                os.unlink(tmp_path)
            _restore_env(saved_env)

    return


def test_property_full_precedence_chain():
    """
        **Validates: Requirements 1.5, 1.6**

        Property: For any configuration, the full precedence chain
        SHALL be: env > file > defaults. When all three sources provide
        a value, the environment variable wins. When only file and
        defaults exist, the file wins. When only defaults exist, the
        default is used.
    """
    for iteration in range(_NUM_ITERATIONS):
        saved_env = _save_and_clear_webworks_env()
        tmp_path = None

        try:
            # Pick three disjoint subsets of keys for each precedence tier
            all_keys = list(_CONFIG_KEYS)
            random.shuffle(all_keys)

            # Split into three groups: env+file, file-only, defaults-only
            split1 = random.randint(1, max(1, len(all_keys) - 2))
            split2 = random.randint(split1 + 1, max(split1 + 1, len(all_keys) - 1))

            env_and_file_keys = all_keys[:split1]
            file_only_keys = all_keys[split1:split2]
            default_only_keys = all_keys[split2:]

            file_config = {}
            expectations = {}

            # Keys with both env and file values — env should win
            for section, key, gen_fn, val_type in env_and_file_keys:
                file_val = gen_fn()
                env_val = gen_fn()
                while env_val == file_val:
                    env_val = gen_fn()

                if section not in file_config:
                    file_config[section] = {}
                file_config[section][key] = file_val

                env_name = _env_key_for(section, key)
                os.environ[env_name] = _env_str_for(env_val, val_type)
                expectations[(section, key)] = env_val

            # Keys with file value only — file should win over default
            for section, key, gen_fn, val_type in file_only_keys:
                file_val = gen_fn()
                default_val = DEFAULT_CONFIG.get(section, {}).get(key)
                while file_val == default_val:
                    file_val = gen_fn()

                if section not in file_config:
                    file_config[section] = {}
                file_config[section][key] = file_val
                expectations[(section, key)] = file_val

            # Keys with only defaults — default should be used
            for section, key, gen_fn, val_type in default_only_keys:
                default_val = DEFAULT_CONFIG.get(section, {}).get(key)
                expectations[(section, key)] = default_val

            with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as tmp:
                json.dump(file_config, tmp)
                tmp_path = tmp.name

            result = load_config(config_path=tmp_path)

            for (section, key), expected in expectations.items():
                actual = result[section][key]
                if actual != expected:
                    errmsg = (
                        "Iteration {}: precedence failed for {}.{}. "
                        "Expected {!r}, got {!r}"
                    ).format(iteration, section, key, expected, actual)
                    raise AssertionError(errmsg)

        finally:
            if tmp_path is not None:
                os.unlink(tmp_path)
            _restore_env(saved_env)

    return


def test_property_non_overridden_values_preserved():
    """
        **Validates: Requirements 1.5, 1.6**

        Property: For any configuration key that is NOT overridden by a
        higher-precedence source, the value from the lower-precedence
        source SHALL be preserved unchanged.
    """
    for iteration in range(_NUM_ITERATIONS):
        saved_env = _save_and_clear_webworks_env()
        tmp_path = None

        try:
            # Pick a random subset of keys to override via file
            all_keys = list(_CONFIG_KEYS)
            random.shuffle(all_keys)
            override_count = random.randint(1, len(all_keys) - 1)
            overridden_keys = all_keys[:override_count]
            preserved_keys = all_keys[override_count:]

            file_config = {}
            for section, key, gen_fn, val_type in overridden_keys:
                file_val = gen_fn()
                default_val = DEFAULT_CONFIG.get(section, {}).get(key)
                while file_val == default_val:
                    file_val = gen_fn()

                if section not in file_config:
                    file_config[section] = {}
                file_config[section][key] = file_val

            with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as tmp:
                json.dump(file_config, tmp)
                tmp_path = tmp.name

            result = load_config(config_path=tmp_path)

            # Verify that non-overridden keys still have their default values
            for section, key, gen_fn, val_type in preserved_keys:
                expected = DEFAULT_CONFIG[section][key]
                actual = result[section][key]
                if actual != expected:
                    errmsg = (
                        "Iteration {}: non-overridden {}.{} should preserve "
                        "default. Expected {!r}, got {!r}"
                    ).format(iteration, section, key, expected, actual)
                    raise AssertionError(errmsg)

        finally:
            if tmp_path is not None:
                os.unlink(tmp_path)
            _restore_env(saved_env)

    return

