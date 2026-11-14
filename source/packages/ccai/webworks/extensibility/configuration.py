"""
    Extension configuration management for the extensibility system.

    This module provides functions for loading, validating, and applying
    defaults to extension-specific configuration. Configuration is
    namespaced by extension name within the application configuration
    (e.g., ``extensions.my_extension.setting``), validated against a
    JSON-schema-like config_schema from the ExtensionManifest, and
    supports environment variable overrides.
"""

import os

from typing import Any, Dict, List, Optional, Tuple

from ccai.webworks.extensibility.exceptions import ExtensionConfigurationError


#: The section of the application configuration that holds the extension
#: settings and, under each extension's name, that extension's configuration.
EXTENSIONS_CONFIG_SECTION = "extensions"


def load_extension_config(
    extension_name: str,
    app_config: Any
) -> Dict[str, Any]:
    """
        Load extension-specific configuration from the application config.

        Configuration is namespaced under ``extensions.<extension_name>``
        in the application configuration. Two shapes of application
        configuration are read:

        * a nested dictionary: ``{"extensions": {"<name>": {...}}}``;
        * a configuration registry with dot-notation keys -- the
          :class:`ConfigRegistry` a web application loads, which flattens a
          nested settings file into keys such as
          ``extensions.<name>.<setting>`` and offers them through
          ``items()``. The keys under the extension's namespace are
          collected and nested again.

        If the extension namespace is not present, or the configuration is
        neither shape, an empty dictionary is returned.

        :param extension_name: The name of the extension.
        :param app_config: The application configuration object.

        :returns: A dictionary of extension-specific configuration values.
    """
    ext_config: Dict[str, Any] = {}

    if isinstance(app_config, dict):
        extensions_section = app_config.get(EXTENSIONS_CONFIG_SECTION, None)
        if isinstance(extensions_section, dict):
            ext_specific = extensions_section.get(extension_name, None)
            if isinstance(ext_specific, dict):
                ext_config = dict(ext_specific)
    else:
        items_method = getattr(app_config, "items", None)
        if callable(items_method):
            pairs = items_method()
            if isinstance(pairs, list):
                ext_config = _collect_namespaced_keys(extension_name, pairs)

    return ext_config


def _collect_namespaced_keys(extension_name: str, pairs: List[Tuple[str, Any]]) -> Dict[str, Any]:
    """
        Collect an extension's settings from dot-notation configuration keys
        and nest them again: ``extensions.<name>.db.host`` becomes
        ``{"db": {"host": ...}}``.

        :param extension_name: The name of the extension.
        :param pairs: The configuration as ``(key, value)`` pairs.

        :returns: The extension's configuration dictionary.
    """
    rtnval: Dict[str, Any] = {}

    prefix = "{}.{}.".format(EXTENSIONS_CONFIG_SECTION, extension_name)

    for pair in pairs:
        key, value = pair
        if not isinstance(key, str) or not key.startswith(prefix):
            continue

        relative_key = key[len(prefix):]
        parts = relative_key.split(".")

        current = rtnval
        for part in parts[:-1]:
            child = current.get(part)
            if not isinstance(child, dict):
                child = {}
                current[part] = child
            current = child

        last_part = parts[-1]
        current[last_part] = value

    return rtnval


def apply_config_defaults(
    config: Dict[str, Any],
    config_schema: Optional[Dict[str, Any]]
) -> Dict[str, Any]:
    """
        Apply default values from the config schema to the configuration.

        For each property defined in the schema that has a ``default``
        value and is not already present in the config, the default
        value is inserted into the config.

        The schema follows a JSON-schema-like structure::

            {
                "properties": {
                    "setting_name": {
                        "type": "string",
                        "default": "default_value"
                    }
                }
            }

        :param config: The current extension configuration dictionary.
        :param config_schema: The JSON-schema-like configuration schema, or None.

        :returns: A new dictionary with defaults applied.
    """
    result = dict(config)

    if config_schema is None:
        return result

    properties = config_schema.get("properties", None)
    if not isinstance(properties, dict):
        return result

    for prop_name, prop_def in properties.items():
        if not isinstance(prop_def, dict):
            continue

        if prop_name not in result and "default" in prop_def:
            result[prop_name] = prop_def["default"]

    return result


def apply_env_overrides(
    extension_name: str,
    config: Dict[str, Any],
    config_schema: Optional[Dict[str, Any]]
) -> Dict[str, Any]:
    """
        Apply environment variable overrides to extension configuration.

        Environment variables are looked up using the pattern
        ``EXTENSION_<UPPER_NAME>_<UPPER_KEY>`` where the extension name
        and key are uppercased and hyphens/dots are replaced with
        underscores.

        Only keys defined in the config schema properties are checked
        for environment variable overrides. The environment variable
        value is coerced to the type specified in the schema when
        possible (string, integer, number, boolean).

        :param extension_name: The name of the extension.
        :param config: The current extension configuration dictionary.
        :param config_schema: The JSON-schema-like configuration schema, or None.

        :returns: A new dictionary with environment variable overrides applied.
    """
    result = dict(config)

    if config_schema is None:
        return result

    properties = config_schema.get("properties", None)
    if not isinstance(properties, dict):
        return result

    # Normalize extension name for env var prefix
    normalized_name = extension_name.upper().replace("-", "_").replace(".", "_")

    for prop_name, prop_def in properties.items():
        if not isinstance(prop_def, dict):
            continue

        normalized_key = prop_name.upper().replace("-", "_").replace(".", "_")
        env_var_name = "EXTENSION_{}_{}".format(normalized_name, normalized_key)

        env_value = os.environ.get(env_var_name, None)
        if env_value is not None:
            prop_type = prop_def.get("type", "string")
            coerced_value = _coerce_env_value(env_value, prop_type)
            result[prop_name] = coerced_value

    return result


def validate_extension_config(
    extension_name: str,
    config: Dict[str, Any],
    config_schema: Optional[Dict[str, Any]]
) -> None:
    """
        Validate extension configuration against the manifest schema.

        Checks that all required properties are present and that
        property values match the expected types defined in the schema.

        :param extension_name: The name of the extension.
        :param config: The extension configuration dictionary.
        :param config_schema: The JSON-schema-like configuration schema, or None.

        :raises: ExtensionConfigurationError
    """
    if config_schema is None:
        return

    properties = config_schema.get("properties", {})
    required_keys = config_schema.get("required", [])

    if not isinstance(properties, dict):
        properties = {}

    if not isinstance(required_keys, list):
        required_keys = []

    # Check required keys are present
    for req_key in required_keys:
        if req_key not in config:
            errmsg = (
                "Extension '{}' is missing required configuration key '{}'"
            ).format(extension_name, req_key)
            raise ExtensionConfigurationError(
                message=errmsg,
                extension_name=extension_name,
                key=req_key
            )

    # Check type constraints for present keys
    for key, value in config.items():
        if key not in properties:
            continue

        prop_def = properties[key]
        if not isinstance(prop_def, dict):
            continue

        expected_type = prop_def.get("type", None)
        if expected_type is None:
            continue

        if not _check_type(value, expected_type):
            errmsg = (
                "Extension '{}' configuration key '{}' has invalid type. "
                "Expected '{}', got '{}'"
            ).format(extension_name, key, expected_type, type(value).__name__)
            raise ExtensionConfigurationError(
                message=errmsg,
                extension_name=extension_name,
                key=key
            )

    return


def _coerce_env_value(value: str, prop_type: str) -> Any:
    """
        Coerce a string environment variable value to the specified type.

        :param value: The string value from the environment variable.
        :param prop_type: The target type name (string, integer, number, boolean).

        :returns: The coerced value.
    """
    if prop_type == "integer":
        try:
            return int(value)
        except ValueError:
            return value

    if prop_type == "number":
        try:
            return float(value)
        except ValueError:
            return value

    if prop_type == "boolean":
        lower_val = value.lower()
        if lower_val in ("true", "1", "yes"):
            return True
        if lower_val in ("false", "0", "no"):
            return False
        return value

    # Default: return as string
    return value


def _check_type(value: Any, expected_type: str) -> bool:
    """
        Check if a value matches the expected JSON-schema type.

        :param value: The value to check.
        :param expected_type: The expected type name (string, integer, number, boolean, object, array).

        :returns: True if the value matches the expected type.
    """
    type_map = {
        "string": str,
        "integer": int,
        "number": (int, float),
        "boolean": bool,
        "object": dict,
        "array": list,
    }

    expected_python_type = type_map.get(expected_type, None)
    if expected_python_type is None:
        # Unknown type, accept any value
        return True

    # Special case: bool is a subclass of int in Python,
    # so we need to exclude booleans from integer checks
    if expected_type == "integer" and isinstance(value, bool):
        return False

    result = isinstance(value, expected_python_type)
    return result
