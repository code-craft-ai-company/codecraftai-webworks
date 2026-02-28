"""
    Tests for the TemplateConfig configuration system.
    
    This module tests the TemplateConfig dataclass including:
    - Default field values
    - Configuration validation
    - Loading from dictionaries
    - Error handling for invalid configuration
"""

from automojo.webworks.templating.config import (
    TemplateConfig,
    VALID_UNDEFINED_BEHAVIORS,
)
from automojo.webworks.templating.exceptions import TemplateConfigurationError


# =============================================================================
# Default Values Tests
# =============================================================================

def test_default_engine_is_jinja2():
    """
        Test that the default engine is jinja2.
    """
    config = TemplateConfig()
    
    if config.engine != "jinja2":
        raise AssertionError(
            f"Expected engine 'jinja2', got '{config.engine}'"
        )
    
    return


def test_default_directories_is_empty_list():
    """
        Test that the default directories is an empty list.
    """
    config = TemplateConfig()
    
    if config.directories != []:
        raise AssertionError(
            f"Expected empty list, got {config.directories}"
        )
    
    return


def test_default_extensions():
    """
        Test that the default extensions include common template types.
    """
    config = TemplateConfig()
    expected = [".html", ".htm", ".xml", ".txt"]
    
    if config.extensions != expected:
        raise AssertionError(
            f"Expected {expected}, got {config.extensions}"
        )
    
    return


def test_default_auto_escape_is_true():
    """
        Test that auto_escape defaults to True.
    """
    config = TemplateConfig()
    
    if config.auto_escape is not True:
        raise AssertionError(
            f"Expected auto_escape True, got {config.auto_escape}"
        )
    
    return


def test_default_cache_enabled_is_true():
    """
        Test that cache_enabled defaults to True.
    """
    config = TemplateConfig()
    
    if config.cache_enabled is not True:
        raise AssertionError(
            f"Expected cache_enabled True, got {config.cache_enabled}"
        )
    
    return


def test_default_cache_size_is_400():
    """
        Test that cache_size defaults to 400.
    """
    config = TemplateConfig()
    
    if config.cache_size != 400:
        raise AssertionError(
            f"Expected cache_size 400, got {config.cache_size}"
        )
    
    return


def test_default_auto_reload_is_false():
    """
        Test that auto_reload defaults to False.
    """
    config = TemplateConfig()
    
    if config.auto_reload is not False:
        raise AssertionError(
            f"Expected auto_reload False, got {config.auto_reload}"
        )
    
    return


def test_default_encoding_is_utf8():
    """
        Test that encoding defaults to utf-8.
    """
    config = TemplateConfig()
    
    if config.encoding != "utf-8":
        raise AssertionError(
            f"Expected encoding 'utf-8', got '{config.encoding}'"
        )
    
    return


def test_default_undefined_behavior_is_silent():
    """
        Test that undefined_behavior defaults to silent.
    """
    config = TemplateConfig()
    
    if config.undefined_behavior != "silent":
        raise AssertionError(
            f"Expected undefined_behavior 'silent', got '{config.undefined_behavior}'"
        )
    
    return


def test_default_engine_options_is_empty_dict():
    """
        Test that engine_options defaults to an empty dict.
    """
    config = TemplateConfig()
    
    if config.engine_options != {}:
        raise AssertionError(
            f"Expected empty dict, got {config.engine_options}"
        )
    
    return


# =============================================================================
# Custom Values Tests
# =============================================================================

def test_custom_engine():
    """
        Test that a custom engine name can be set.
    """
    config = TemplateConfig(engine="mako")
    
    if config.engine != "mako":
        raise AssertionError(
            f"Expected engine 'mako', got '{config.engine}'"
        )
    
    return


def test_custom_directories():
    """
        Test that custom directories can be set.
    """
    dirs = ["/app/templates", "/app/shared"]
    config = TemplateConfig(directories=dirs)
    
    if config.directories != dirs:
        raise AssertionError(
            f"Expected {dirs}, got {config.directories}"
        )
    
    return


def test_custom_cache_size():
    """
        Test that a custom cache_size can be set.
    """
    config = TemplateConfig(cache_size=200)
    
    if config.cache_size != 200:
        raise AssertionError(
            f"Expected cache_size 200, got {config.cache_size}"
        )
    
    return


def test_custom_engine_options():
    """
        Test that custom engine_options can be set.
    """
    options = {"trim_blocks": True, "lstrip_blocks": True}
    config = TemplateConfig(engine_options=options)
    
    if config.engine_options != options:
        raise AssertionError(
            f"Expected {options}, got {config.engine_options}"
        )
    
    return


# =============================================================================
# validate() Method Tests
# =============================================================================

def test_validate_passes_with_defaults():
    """
        Test that validate() passes with default configuration.
    """
    config = TemplateConfig()
    config.validate()
    
    return


def test_validate_passes_with_valid_custom_config():
    """
        Test that validate() passes with valid custom configuration.
    """
    config = TemplateConfig(
        engine="mako",
        directories=["/app/templates"],
        cache_size=100,
        undefined_behavior="strict",
        encoding="latin-1"
    )
    config.validate()
    
    return


def test_validate_raises_for_empty_engine():
    """
        Test that validate() raises TemplateConfigurationError for empty engine.
    """
    config = TemplateConfig(engine="")
    
    try:
        config.validate()
        raise AssertionError("Expected TemplateConfigurationError to be raised")
    except TemplateConfigurationError as exc:
        if exc.field_name != "engine":
            raise AssertionError(
                f"Expected field_name 'engine', got '{exc.field_name}'"
            )
    
    return


def test_validate_raises_for_whitespace_engine():
    """
        Test that validate() raises TemplateConfigurationError for whitespace-only engine.
    """
    config = TemplateConfig(engine="   ")
    
    try:
        config.validate()
        raise AssertionError("Expected TemplateConfigurationError to be raised")
    except TemplateConfigurationError as exc:
        if exc.field_name != "engine":
            raise AssertionError(
                f"Expected field_name 'engine', got '{exc.field_name}'"
            )
    
    return


def test_validate_raises_for_non_list_directories():
    """
        Test that validate() raises TemplateConfigurationError for non-list directories.
    """
    config = TemplateConfig()
    config.directories = "not-a-list"
    
    try:
        config.validate()
        raise AssertionError("Expected TemplateConfigurationError to be raised")
    except TemplateConfigurationError as exc:
        if exc.field_name != "directories":
            raise AssertionError(
                f"Expected field_name 'directories', got '{exc.field_name}'"
            )
    
    return


def test_validate_raises_for_zero_cache_size():
    """
        Test that validate() raises TemplateConfigurationError for zero cache_size.
    """
    config = TemplateConfig(cache_size=0)
    
    try:
        config.validate()
        raise AssertionError("Expected TemplateConfigurationError to be raised")
    except TemplateConfigurationError as exc:
        if exc.field_name != "cache_size":
            raise AssertionError(
                f"Expected field_name 'cache_size', got '{exc.field_name}'"
            )
    
    return


def test_validate_raises_for_negative_cache_size():
    """
        Test that validate() raises TemplateConfigurationError for negative cache_size.
    """
    config = TemplateConfig(cache_size=-10)
    
    try:
        config.validate()
        raise AssertionError("Expected TemplateConfigurationError to be raised")
    except TemplateConfigurationError as exc:
        if exc.field_name != "cache_size":
            raise AssertionError(
                f"Expected field_name 'cache_size', got '{exc.field_name}'"
            )
    
    return


def test_validate_raises_for_invalid_undefined_behavior():
    """
        Test that validate() raises TemplateConfigurationError for invalid undefined_behavior.
    """
    config = TemplateConfig(undefined_behavior="invalid")
    
    try:
        config.validate()
        raise AssertionError("Expected TemplateConfigurationError to be raised")
    except TemplateConfigurationError as exc:
        if exc.field_name != "undefined_behavior":
            raise AssertionError(
                f"Expected field_name 'undefined_behavior', got '{exc.field_name}'"
            )
    
    return


def test_validate_raises_for_empty_encoding():
    """
        Test that validate() raises TemplateConfigurationError for empty encoding.
    """
    config = TemplateConfig(encoding="")
    
    try:
        config.validate()
        raise AssertionError("Expected TemplateConfigurationError to be raised")
    except TemplateConfigurationError as exc:
        if exc.field_name != "encoding":
            raise AssertionError(
                f"Expected field_name 'encoding', got '{exc.field_name}'"
            )
    
    return


def test_validate_accepts_strict_undefined_behavior():
    """
        Test that validate() accepts strict undefined_behavior.
    """
    config = TemplateConfig(undefined_behavior="strict")
    config.validate()
    
    return


def test_validate_accepts_debug_undefined_behavior():
    """
        Test that validate() accepts debug undefined_behavior.
    """
    config = TemplateConfig(undefined_behavior="debug")
    config.validate()
    
    return


def test_validate_accepts_silent_undefined_behavior():
    """
        Test that validate() accepts silent undefined_behavior.
    """
    config = TemplateConfig(undefined_behavior="silent")
    config.validate()
    
    return


# =============================================================================
# from_dict() Method Tests
# =============================================================================

def test_from_dict_with_empty_dict():
    """
        Test that from_dict() with empty dict returns defaults.
    """
    config = TemplateConfig.from_dict({})
    
    if config.engine != "jinja2":
        raise AssertionError(
            f"Expected engine 'jinja2', got '{config.engine}'"
        )
    
    if config.cache_size != 400:
        raise AssertionError(
            f"Expected cache_size 400, got {config.cache_size}"
        )
    
    return


def test_from_dict_with_all_fields():
    """
        Test that from_dict() sets all known fields.
    """
    data = {
        "engine": "mako",
        "directories": ["/templates"],
        "extensions": [".html"],
        "auto_escape": False,
        "cache_enabled": False,
        "cache_size": 100,
        "auto_reload": True,
        "encoding": "latin-1",
        "undefined_behavior": "strict",
        "engine_options": {"trim_blocks": True}
    }
    config = TemplateConfig.from_dict(data)
    
    if config.engine != "mako":
        raise AssertionError(
            f"Expected engine 'mako', got '{config.engine}'"
        )
    
    if config.directories != ["/templates"]:
        raise AssertionError(
            f"Expected ['/templates'], got {config.directories}"
        )
    
    if config.extensions != [".html"]:
        raise AssertionError(
            f"Expected ['.html'], got {config.extensions}"
        )
    
    if config.auto_escape is not False:
        raise AssertionError(
            f"Expected auto_escape False, got {config.auto_escape}"
        )
    
    if config.cache_enabled is not False:
        raise AssertionError(
            f"Expected cache_enabled False, got {config.cache_enabled}"
        )
    
    if config.cache_size != 100:
        raise AssertionError(
            f"Expected cache_size 100, got {config.cache_size}"
        )
    
    if config.auto_reload is not True:
        raise AssertionError(
            f"Expected auto_reload True, got {config.auto_reload}"
        )
    
    if config.encoding != "latin-1":
        raise AssertionError(
            f"Expected encoding 'latin-1', got '{config.encoding}'"
        )
    
    if config.undefined_behavior != "strict":
        raise AssertionError(
            f"Expected undefined_behavior 'strict', got '{config.undefined_behavior}'"
        )
    
    if config.engine_options != {"trim_blocks": True}:
        raise AssertionError(
            f"Expected engine_options with trim_blocks, got {config.engine_options}"
        )
    
    return


def test_from_dict_ignores_unknown_keys():
    """
        Test that from_dict() ignores unknown keys in the dictionary.
    """
    data = {
        "engine": "jinja2",
        "unknown_key": "should_be_ignored",
        "another_unknown": 42
    }
    config = TemplateConfig.from_dict(data)
    
    if config.engine != "jinja2":
        raise AssertionError(
            f"Expected engine 'jinja2', got '{config.engine}'"
        )
    
    if hasattr(config, "unknown_key"):
        raise AssertionError("Config should not have 'unknown_key' attribute")
    
    return


def test_from_dict_with_partial_fields():
    """
        Test that from_dict() with partial fields uses defaults for the rest.
    """
    data = {
        "engine": "mako",
        "cache_size": 200
    }
    config = TemplateConfig.from_dict(data)
    
    if config.engine != "mako":
        raise AssertionError(
            f"Expected engine 'mako', got '{config.engine}'"
        )
    
    if config.cache_size != 200:
        raise AssertionError(
            f"Expected cache_size 200, got {config.cache_size}"
        )
    
    # Defaults should be preserved
    if config.auto_escape is not True:
        raise AssertionError(
            f"Expected auto_escape True, got {config.auto_escape}"
        )
    
    if config.encoding != "utf-8":
        raise AssertionError(
            f"Expected encoding 'utf-8', got '{config.encoding}'"
        )
    
    return


def test_from_dict_with_nested_engine_options():
    """
        Test that from_dict() supports nested engine_options.
    """
    data = {
        "engine_options": {
            "trim_blocks": True,
            "lstrip_blocks": True,
            "extensions": ["jinja2.ext.do"]
        }
    }
    config = TemplateConfig.from_dict(data)
    
    if config.engine_options.get("trim_blocks") is not True:
        raise AssertionError(
            f"Expected trim_blocks True, got {config.engine_options.get('trim_blocks')}"
        )
    
    if config.engine_options.get("lstrip_blocks") is not True:
        raise AssertionError(
            f"Expected lstrip_blocks True, got {config.engine_options.get('lstrip_blocks')}"
        )
    
    expected_extensions = ["jinja2.ext.do"]
    if config.engine_options.get("extensions") != expected_extensions:
        raise AssertionError(
            f"Expected extensions {expected_extensions}, "
            f"got {config.engine_options.get('extensions')}"
        )
    
    return


# =============================================================================
# Configuration Validation Error Details Tests
# =============================================================================

def test_validate_error_message_includes_field_name():
    """
        Test that validation errors include the field name.
    """
    config = TemplateConfig(engine="")
    
    try:
        config.validate()
        raise AssertionError("Expected TemplateConfigurationError to be raised")
    except TemplateConfigurationError as exc:
        error_message = str(exc)
        if "engine" not in error_message:
            raise AssertionError(
                f"Expected 'engine' in error message, got: {error_message}"
            )
    
    return


def test_validate_error_for_non_integer_cache_size():
    """
        Test that validate() raises for non-integer cache_size.
    """
    config = TemplateConfig()
    config.cache_size = 3.5
    
    try:
        config.validate()
        raise AssertionError("Expected TemplateConfigurationError to be raised")
    except TemplateConfigurationError as exc:
        if exc.field_name != "cache_size":
            raise AssertionError(
                f"Expected field_name 'cache_size', got '{exc.field_name}'"
            )
    
    return


def test_validate_error_for_non_string_engine():
    """
        Test that validate() raises for non-string engine.
    """
    config = TemplateConfig()
    config.engine = 123
    
    try:
        config.validate()
        raise AssertionError("Expected TemplateConfigurationError to be raised")
    except TemplateConfigurationError as exc:
        if exc.field_name != "engine":
            raise AssertionError(
                f"Expected field_name 'engine', got '{exc.field_name}'"
            )
    
    return


def test_validate_error_for_non_string_encoding():
    """
        Test that validate() raises for non-string encoding.
    """
    config = TemplateConfig()
    config.encoding = 42
    
    try:
        config.validate()
        raise AssertionError("Expected TemplateConfigurationError to be raised")
    except TemplateConfigurationError as exc:
        if exc.field_name != "encoding":
            raise AssertionError(
                f"Expected field_name 'encoding', got '{exc.field_name}'"
            )
    
    return


# =============================================================================
# Dataclass Behavior Tests
# =============================================================================

def test_config_instances_are_independent():
    """
        Test that separate TemplateConfig instances do not share mutable defaults.
    """
    config_a = TemplateConfig()
    config_b = TemplateConfig()
    
    config_a.directories.append("/app/templates")
    
    if len(config_b.directories) != 0:
        raise AssertionError(
            "Modifying one config's directories should not affect another"
        )
    
    return


def test_config_engine_options_are_independent():
    """
        Test that separate TemplateConfig instances do not share engine_options.
    """
    config_a = TemplateConfig()
    config_b = TemplateConfig()
    
    config_a.engine_options["trim_blocks"] = True
    
    if "trim_blocks" in config_b.engine_options:
        raise AssertionError(
            "Modifying one config's engine_options should not affect another"
        )
    
    return
