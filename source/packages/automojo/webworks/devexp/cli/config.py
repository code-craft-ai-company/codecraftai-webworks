"""
    Configuration loading for the webworks CLI.

    This module provides functions for loading and merging configuration
    from multiple sources. Configuration is resolved in the following
    order of precedence (highest to lowest):

    1. Environment variables with the ``WEBWORKS_`` prefix
    2. Configuration file (JSON format)
    3. Default configuration values

    Environment variables use the format ``WEBWORKS_SECTION_KEY`` to map
    to nested configuration keys. For example, ``WEBWORKS_SERVER_HOST``
    maps to ``config["server"]["host"]``.
"""

import copy
import json
import os

from typing import Any, Dict, Optional


DEFAULT_CONFIG: Dict[str, Any] = {
    "server": {
        "host": "127.0.0.1",
        "port": 8000,
        "debug": True,
        "reload": False,
    },
    "logging": {
        "level": "DEBUG",
        "format": "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        "colors": True,
    },
    "debug": {
        "interactive": False,
        "pin": None,
        "timeout": 300,
    },
    "inspector": {
        "enabled": False,
        "max_requests": 100,
        "max_body_size": 10240,
    },
}

ENV_PREFIX = "WEBWORKS_"


def load_config_from_file(config_path: str) -> Dict[str, Any]:
    """
        Load configuration from a JSON file.

        Reads the file at the given path and parses it as JSON. If the
        file does not exist or cannot be parsed, an empty dictionary is
        returned.

        :param config_path: Path to the JSON configuration file.

        :returns: A dictionary of configuration values from the file.
    """
    if not os.path.isfile(config_path):
        return {}

    try:
        with open(config_path, "r") as config_file:
            data = json.load(config_file)
    except (json.JSONDecodeError, OSError):
        return {}

    if not isinstance(data, dict):
        return {}

    return data


def load_config_from_env() -> Dict[str, Any]:
    """
        Load configuration from environment variables.

        Scans environment variables for entries with the ``WEBWORKS_``
        prefix. The variable name is split on underscores after the
        prefix to determine the section and key. For example,
        ``WEBWORKS_SERVER_HOST`` maps to ``config["server"]["host"]``.

        Values are coerced to match the types in the default
        configuration when possible. Boolean strings (``true``,
        ``false``) are converted to booleans. Numeric strings are
        converted to integers. The string ``none`` is converted to
        None.

        :returns: A nested dictionary of configuration values from
            environment variables.
    """
    config: Dict[str, Any] = {}

    for env_key, env_value in os.environ.items():
        if not env_key.startswith(ENV_PREFIX):
            continue

        suffix = env_key[len(ENV_PREFIX):]
        parts = suffix.lower().split("_", 1)

        if len(parts) != 2:
            continue

        section = parts[0]
        key = parts[1]

        coerced_value = _coerce_env_value(env_value, section, key)

        if section not in config:
            config[section] = {}

        config[section][key] = coerced_value

    return config


def _coerce_env_value(value: str, section: str, key: str) -> Any:
    """
        Coerce an environment variable string value to the appropriate
        Python type based on the default configuration.

        If the section and key exist in the default configuration, the
        value is coerced to match the type of the default. Otherwise,
        the raw string value is returned.

        :param value: The raw string value from the environment.
        :param section: The configuration section name.
        :param key: The configuration key name.

        :returns: The coerced value.
    """
    default_section = DEFAULT_CONFIG.get(section)
    if default_section is None:
        return value

    default_value = default_section.get(key)

    if default_value is None:
        # The default is None, so check for the string "none"
        lower_value = value.lower()
        if lower_value == "none":
            return None
        return value

    if isinstance(default_value, bool):
        return value.lower() in ("true", "1", "yes")

    if isinstance(default_value, int):
        try:
            return int(value)
        except ValueError:
            return value

    return value


def merge_configs(base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
    """
        Deep merge two configuration dictionaries.

        Values from the override dictionary take precedence over values
        in the base dictionary. Nested dictionaries are merged
        recursively rather than replaced entirely.

        :param base: The base configuration dictionary.
        :param override: The override configuration dictionary.

        :returns: A new dictionary with merged values.
    """
    merged = copy.deepcopy(base)

    for key, value in override.items():
        if key in merged and isinstance(merged[key], dict) and isinstance(value, dict):
            merged[key] = merge_configs(merged[key], value)
        else:
            merged[key] = copy.deepcopy(value)

    return merged


def load_config(config_path: Optional[str] = None) -> Dict[str, Any]:
    """
        Load the full configuration by merging defaults, file config,
        and environment variable overrides.

        The merge order ensures that environment variables take
        precedence over file configuration, which takes precedence
        over default values.

        :param config_path: Optional path to a JSON configuration file.

        :returns: The fully merged configuration dictionary.
    """
    config = copy.deepcopy(DEFAULT_CONFIG)

    if config_path is not None:
        file_config = load_config_from_file(config_path)
        config = merge_configs(config, file_config)

    env_config = load_config_from_env()
    config = merge_configs(config, env_config)

    return config
