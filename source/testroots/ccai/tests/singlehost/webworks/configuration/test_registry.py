"""
    Tests for the configuration registry module.
    
    This module contains unit tests and property tests for the ConfigRegistry class.
"""

import os
from pathlib import Path
from typing import Any, Dict, List

from ccai.webworks.configuration import (
    ConfigRegistry,
    ConfigSchema,
    ConfigSource,
    ConfigSourceType,
    ConfigValue,
    ConfigChangeEvent,
    ConfigurationError,
    ConfigurationValidationError,
    ConfigurationFrozenError,
    DEFAULT_PRECEDENCE
)


# =============================================================================
# Helper Classes for Testing
# =============================================================================

class MockConfigSource(ConfigSource):
    """
        A mock configuration source for testing.
    """
    
    def __init__(
        self,
        values: Dict[str, Any],
        source_type: ConfigSourceType = ConfigSourceType.FILE
    ):
        self._values = values
        self._source_type = source_type
    
    def load(self) -> Dict[str, Any]:
        return dict(self._values)
    
    @property
    def source_type(self) -> ConfigSourceType:
        return self._source_type


# =============================================================================
# Unit Tests for ConfigRegistry Creation
# =============================================================================

def test_config_registry_creation_default():
    """
        Test that ConfigRegistry can be created with default settings.
    """
    registry = ConfigRegistry()
    
    if registry.schema is not None:
        errmsg = f"Expected schema None, got {registry.schema}"
        raise AssertionError(errmsg)
    
    if registry.precedence != DEFAULT_PRECEDENCE:
        errmsg = f"Expected default precedence, got {registry.precedence}"
        raise AssertionError(errmsg)
    
    if registry.is_frozen:
        errmsg = "Expected is_frozen False"
        raise AssertionError(errmsg)
    
    if registry.is_loaded:
        errmsg = "Expected is_loaded False"
        raise AssertionError(errmsg)
    
    return


def test_config_registry_creation_with_schema():
    """
        Test that ConfigRegistry can be created with a schema.
    """
    schema = ConfigSchema()
    schema.define("test.key", str, default="value")
    
    registry = ConfigRegistry(schema=schema)
    
    if registry.schema is not schema:
        errmsg = "Expected schema to be the provided schema"
        raise AssertionError(errmsg)
    
    return


def test_config_registry_creation_with_custom_precedence():
    """
        Test that ConfigRegistry can be created with custom precedence.
    """
    custom_precedence = [
        ConfigSourceType.OVERRIDE,
        ConfigSourceType.FILE,
        ConfigSourceType.ENVIRONMENT,
        ConfigSourceType.DEFAULT
    ]
    
    registry = ConfigRegistry(precedence=custom_precedence)
    
    if registry.precedence != custom_precedence:
        errmsg = f"Expected custom precedence, got {registry.precedence}"
        raise AssertionError(errmsg)
    
    return


# =============================================================================
# Unit Tests for Source Registration
# =============================================================================

def test_config_registry_register_source():
    """
        Test that sources can be registered.
    """
    registry = ConfigRegistry()
    source = MockConfigSource({"key": "value"})
    
    registry.register_source(source)
    
    # Load to verify source was registered
    registry.load()
    
    value = registry.get("key")
    if value != "value":
        errmsg = f"Expected value 'value', got {value}"
        raise AssertionError(errmsg)
    
    return


def test_config_registry_register_multiple_sources_same_type():
    """
        Test that multiple sources of the same type can be registered.
    """
    registry = ConfigRegistry()
    
    source1 = MockConfigSource({"key1": "value1", "shared": "from_source1"})
    source2 = MockConfigSource({"key2": "value2", "shared": "from_source2"})
    
    registry.register_source(source1)
    registry.register_source(source2)
    
    registry.load()
    
    # Both keys should be present
    if registry.get("key1") != "value1":
        errmsg = f"Expected key1='value1', got {registry.get('key1')}"
        raise AssertionError(errmsg)
    
    if registry.get("key2") != "value2":
        errmsg = f"Expected key2='value2', got {registry.get('key2')}"
        raise AssertionError(errmsg)
    
    # Later source should win for shared key
    if registry.get("shared") != "from_source2":
        errmsg = f"Expected shared='from_source2', got {registry.get('shared')}"
        raise AssertionError(errmsg)
    
    return


def test_config_registry_register_source_frozen_raises():
    """
        Test that registering a source when frozen raises error.
    """
    registry = ConfigRegistry()
    registry.freeze()
    
    source = MockConfigSource({"key": "value"})
    
    try:
        registry.register_source(source)
        raise AssertionError("Expected ConfigurationFrozenError")
    except ConfigurationFrozenError:
        pass
    
    return


# =============================================================================
# Unit Tests for Configuration Loading
# =============================================================================

def test_config_registry_load_returns_self():
    """
        Test that load() returns self for method chaining.
    """
    registry = ConfigRegistry()
    result = registry.load()
    
    if result is not registry:
        errmsg = "Expected load() to return self"
        raise AssertionError(errmsg)
    
    return


def test_config_registry_load_sets_loaded_flag():
    """
        Test that load() sets the is_loaded flag.
    """
    registry = ConfigRegistry()
    
    if registry.is_loaded:
        errmsg = "Expected is_loaded False before load"
        raise AssertionError(errmsg)
    
    registry.load()
    
    if not registry.is_loaded:
        errmsg = "Expected is_loaded True after load"
        raise AssertionError(errmsg)
    
    return


def test_config_registry_load_with_schema_defaults():
    """
        Test that schema defaults are loaded.
    """
    schema = ConfigSchema()
    schema.define("database.host", str, default="localhost")
    schema.define("database.port", int, default=5432)
    
    registry = ConfigRegistry(schema=schema)
    registry.load()
    
    if registry.get("database.host") != "localhost":
        errmsg = f"Expected database.host='localhost', got {registry.get('database.host')}"
        raise AssertionError(errmsg)
    
    if registry.get("database.port") != 5432:
        errmsg = f"Expected database.port=5432, got {registry.get('database.port')}"
        raise AssertionError(errmsg)
    
    return


def test_config_registry_get_auto_loads():
    """
        Test that get() auto-loads if not loaded.
    """
    schema = ConfigSchema()
    schema.define("key", str, default="value")
    
    registry = ConfigRegistry(schema=schema)
    
    # Don't call load() explicitly
    value = registry.get("key")
    
    if value != "value":
        errmsg = f"Expected value 'value', got {value}"
        raise AssertionError(errmsg)
    
    if not registry.is_loaded:
        errmsg = "Expected is_loaded True after get()"
        raise AssertionError(errmsg)
    
    return


def test_config_registry_get_with_default():
    """
        Test that get() returns default for missing keys.
    """
    registry = ConfigRegistry()
    registry.load()
    
    value = registry.get("missing.key", "default_value")
    
    if value != "default_value":
        errmsg = f"Expected 'default_value', got {value}"
        raise AssertionError(errmsg)
    
    return


def test_config_registry_keys():
    """
        Test that keys() returns all configuration keys.
    """
    registry = ConfigRegistry()
    source = MockConfigSource({"key1": "value1", "key2": "value2"})
    registry.register_source(source)
    registry.load()
    
    keys = registry.keys()
    
    if "key1" not in keys:
        errmsg = "Expected 'key1' in keys"
        raise AssertionError(errmsg)
    
    if "key2" not in keys:
        errmsg = "Expected 'key2' in keys"
        raise AssertionError(errmsg)
    
    return


def test_config_registry_items():
    """
        Test that items() returns all key-value pairs.
    """
    registry = ConfigRegistry()
    source = MockConfigSource({"key1": "value1", "key2": "value2"})
    registry.register_source(source)
    registry.load()
    
    items = registry.items()
    items_dict = dict(items)
    
    if items_dict.get("key1") != "value1":
        errmsg = f"Expected key1='value1', got {items_dict.get('key1')}"
        raise AssertionError(errmsg)
    
    if items_dict.get("key2") != "value2":
        errmsg = f"Expected key2='value2', got {items_dict.get('key2')}"
        raise AssertionError(errmsg)
    
    return


# =============================================================================
# Property Tests for Source Precedence
# =============================================================================

def test_property_source_precedence():
    """
        Property 7: Source Precedence
        
        *For any* configuration key that exists in multiple sources, the value
        from the highest-precedence source according to the configured precedence
        order SHALL be returned.
        
        **Validates: Requirements 2.6, 2.9**
        
        This test verifies that when the same key exists in multiple sources,
        the value from the source with highest precedence is used.
    """
    import random
    import string
    
    def generate_random_key():
        """Generate a random configuration key."""
        parts = random.randint(1, 3)
        return ".".join(
            "".join(random.choices(string.ascii_lowercase, k=random.randint(3, 8)))
            for _ in range(parts)
        )
    
    def generate_random_value():
        """Generate a random configuration value."""
        return "".join(random.choices(string.ascii_letters + string.digits, k=random.randint(5, 15)))
    
    # Run 100 iterations
    for iteration in range(100):
        # Generate a random key
        key = generate_random_key()
        
        # Generate different values for different source types
        env_value = f"env_{generate_random_value()}"
        file_value = f"file_{generate_random_value()}"
        secrets_value = f"secrets_{generate_random_value()}"
        
        # Create sources with the same key but different values
        env_source = MockConfigSource(
            {key: env_value},
            source_type=ConfigSourceType.ENVIRONMENT
        )
        file_source = MockConfigSource(
            {key: file_value},
            source_type=ConfigSourceType.FILE
        )
        secrets_source = MockConfigSource(
            {key: secrets_value},
            source_type=ConfigSourceType.SECRETS
        )
        
        # Create registry with default precedence
        # Default: OVERRIDE > ENVIRONMENT > SECRETS > FILE > DEFAULT
        registry = ConfigRegistry()
        registry.register_source(env_source)
        registry.register_source(file_source)
        registry.register_source(secrets_source)
        registry.load()
        
        # Environment should win (highest precedence among registered sources)
        result = registry.get(key)
        if result != env_value:
            errmsg = (
                f"Iteration {iteration}: Expected environment value '{env_value}' "
                f"to take precedence, got '{result}'"
            )
            raise AssertionError(errmsg)
        
        # Verify the source metadata
        config_value = registry.get_value(key)
        if config_value.source != ConfigSourceType.ENVIRONMENT:
            errmsg = (
                f"Iteration {iteration}: Expected source ENVIRONMENT, "
                f"got {config_value.source}"
            )
            raise AssertionError(errmsg)
    
    return


def test_property_source_precedence_file_over_default():
    """
        Property 7: Source Precedence (File over Default)
        
        Verifies that FILE source takes precedence over DEFAULT (schema defaults).
        
        **Validates: Requirements 2.6, 2.9**
    """
    import random
    import string
    
    # Run 100 iterations
    for iteration in range(100):
        # Generate random key and values
        key = "test." + "".join(random.choices(string.ascii_lowercase, k=6))
        default_value = f"default_{random.randint(1, 1000)}"
        file_value = f"file_{random.randint(1, 1000)}"
        
        # Create schema with default
        schema = ConfigSchema()
        schema.define(key, str, default=default_value)
        
        # Create file source with different value
        file_source = MockConfigSource(
            {key: file_value},
            source_type=ConfigSourceType.FILE
        )
        
        # Create registry
        registry = ConfigRegistry(schema=schema)
        registry.register_source(file_source)
        registry.load()
        
        # File should win over default
        result = registry.get(key)
        if result != file_value:
            errmsg = (
                f"Iteration {iteration}: Expected file value '{file_value}' "
                f"to take precedence over default '{default_value}', got '{result}'"
            )
            raise AssertionError(errmsg)
    
    return


def test_property_source_precedence_secrets_over_file():
    """
        Property 7: Source Precedence (Secrets over File)
        
        Verifies that SECRETS source takes precedence over FILE source.
        
        **Validates: Requirements 2.6, 2.9**
    """
    import random
    import string
    
    # Run 100 iterations
    for iteration in range(100):
        # Generate random key and values
        key = "db." + "".join(random.choices(string.ascii_lowercase, k=6))
        file_value = f"file_{random.randint(1, 1000)}"
        secrets_value = f"secrets_{random.randint(1, 1000)}"
        
        # Create sources
        file_source = MockConfigSource(
            {key: file_value},
            source_type=ConfigSourceType.FILE
        )
        secrets_source = MockConfigSource(
            {key: secrets_value},
            source_type=ConfigSourceType.SECRETS
        )
        
        # Create registry
        registry = ConfigRegistry()
        registry.register_source(file_source)
        registry.register_source(secrets_source)
        registry.load()
        
        # Secrets should win over file
        result = registry.get(key)
        if result != secrets_value:
            errmsg = (
                f"Iteration {iteration}: Expected secrets value '{secrets_value}' "
                f"to take precedence over file '{file_value}', got '{result}'"
            )
            raise AssertionError(errmsg)
    
    return


# =============================================================================
# Unit Tests for Override Mechanism
# =============================================================================

def test_config_registry_override():
    """
        Test that override() sets a value with highest precedence.
    """
    registry = ConfigRegistry()
    source = MockConfigSource({"key": "original"})
    registry.register_source(source)
    registry.load()
    
    # Override the value
    registry.override("key", "overridden")
    
    if registry.get("key") != "overridden":
        errmsg = f"Expected 'overridden', got {registry.get('key')}"
        raise AssertionError(errmsg)
    
    return


def test_config_registry_override_new_key():
    """
        Test that override() can set a new key.
    """
    registry = ConfigRegistry()
    registry.load()
    
    registry.override("new.key", "new_value")
    
    if registry.get("new.key") != "new_value":
        errmsg = f"Expected 'new_value', got {registry.get('new.key')}"
        raise AssertionError(errmsg)
    
    return


def test_config_registry_override_frozen_raises():
    """
        Test that override() raises error when frozen.
    """
    registry = ConfigRegistry()
    registry.load()
    registry.freeze()
    
    try:
        registry.override("key", "value")
        raise AssertionError("Expected ConfigurationFrozenError")
    except ConfigurationFrozenError:
        pass
    
    return


def test_config_registry_clear_override():
    """
        Test that clear_override() removes an override.
    """
    schema = ConfigSchema()
    schema.define("key", str, default="default")
    
    registry = ConfigRegistry(schema=schema)
    registry.load()
    
    # Set override
    registry.override("key", "overridden")
    if registry.get("key") != "overridden":
        errmsg = f"Expected 'overridden', got {registry.get('key')}"
        raise AssertionError(errmsg)
    
    # Clear override
    registry.clear_override("key")
    
    # Should fall back to default
    if registry.get("key") != "default":
        errmsg = f"Expected 'default' after clear, got {registry.get('key')}"
        raise AssertionError(errmsg)
    
    return


def test_config_registry_clear_all_overrides():
    """
        Test that clear_all_overrides() removes all overrides.
    """
    schema = ConfigSchema()
    schema.define("key1", str, default="default1")
    schema.define("key2", str, default="default2")
    
    registry = ConfigRegistry(schema=schema)
    registry.load()
    
    # Set overrides
    registry.override("key1", "override1")
    registry.override("key2", "override2")
    
    # Clear all
    registry.clear_all_overrides()
    
    # Should fall back to defaults
    if registry.get("key1") != "default1":
        errmsg = f"Expected 'default1', got {registry.get('key1')}"
        raise AssertionError(errmsg)
    
    if registry.get("key2") != "default2":
        errmsg = f"Expected 'default2', got {registry.get('key2')}"
        raise AssertionError(errmsg)
    
    return


# =============================================================================
# Property Tests for Runtime Override Precedence
# =============================================================================

def test_property_runtime_override_precedence():
    """
        Property 22: Runtime Override Precedence
        
        *For any* programmatic override, the override value SHALL take precedence
        over all other sources when accessing that key.
        
        **Validates: Requirements 6.1, 6.2**
        
        This test verifies that runtime overrides always take highest precedence.
    """
    import random
    import string
    
    def generate_random_value():
        """Generate a random configuration value."""
        return "".join(random.choices(string.ascii_letters + string.digits, k=random.randint(5, 15)))
    
    # Run 100 iterations
    for iteration in range(100):
        # Generate random key and values
        key = "test." + "".join(random.choices(string.ascii_lowercase, k=6))
        default_value = f"default_{generate_random_value()}"
        env_value = f"env_{generate_random_value()}"
        file_value = f"file_{generate_random_value()}"
        secrets_value = f"secrets_{generate_random_value()}"
        override_value = f"override_{generate_random_value()}"
        
        # Create schema with default
        schema = ConfigSchema()
        schema.define(key, str, default=default_value)
        
        # Create sources with the same key
        env_source = MockConfigSource(
            {key: env_value},
            source_type=ConfigSourceType.ENVIRONMENT
        )
        file_source = MockConfigSource(
            {key: file_value},
            source_type=ConfigSourceType.FILE
        )
        secrets_source = MockConfigSource(
            {key: secrets_value},
            source_type=ConfigSourceType.SECRETS
        )
        
        # Create registry with all sources
        registry = ConfigRegistry(schema=schema)
        registry.register_source(env_source)
        registry.register_source(file_source)
        registry.register_source(secrets_source)
        registry.load()
        
        # Apply override
        registry.override(key, override_value)
        
        # Override should win over all sources
        result = registry.get(key)
        if result != override_value:
            errmsg = (
                f"Iteration {iteration}: Expected override value '{override_value}' "
                f"to take precedence over all sources, got '{result}'"
            )
            raise AssertionError(errmsg)
        
        # Verify the source metadata
        config_value = registry.get_value(key)
        if config_value.source != ConfigSourceType.OVERRIDE:
            errmsg = (
                f"Iteration {iteration}: Expected source OVERRIDE, "
                f"got {config_value.source}"
            )
            raise AssertionError(errmsg)
        
        if not config_value.is_override:
            errmsg = f"Iteration {iteration}: Expected is_override=True"
            raise AssertionError(errmsg)
    
    return


def test_property_override_persists_across_reload():
    """
        Property 22: Runtime Override Precedence (Persistence)
        
        Verifies that overrides persist across configuration reloads.
        
        **Validates: Requirements 6.1, 6.2**
    """
    import random
    import string
    
    # Run 100 iterations
    for iteration in range(100):
        # Generate random key and values
        key = "persist." + "".join(random.choices(string.ascii_lowercase, k=6))
        file_value = f"file_{random.randint(1, 1000)}"
        override_value = f"override_{random.randint(1, 1000)}"
        
        # Create source
        file_source = MockConfigSource(
            {key: file_value},
            source_type=ConfigSourceType.FILE
        )
        
        # Create registry
        registry = ConfigRegistry()
        registry.register_source(file_source)
        registry.load()
        
        # Apply override
        registry.override(key, override_value)
        
        # Reload configuration
        registry.load()
        
        # Override should still be in effect
        result = registry.get(key)
        if result != override_value:
            errmsg = (
                f"Iteration {iteration}: Expected override '{override_value}' "
                f"to persist after reload, got '{result}'"
            )
            raise AssertionError(errmsg)
    
    return


# =============================================================================
# Unit Tests for Freeze Functionality
# =============================================================================

def test_config_registry_freeze():
    """
        Test that freeze() sets the frozen flag.
    """
    registry = ConfigRegistry()
    
    if registry.is_frozen:
        errmsg = "Expected is_frozen False before freeze"
        raise AssertionError(errmsg)
    
    registry.freeze()
    
    if not registry.is_frozen:
        errmsg = "Expected is_frozen True after freeze"
        raise AssertionError(errmsg)
    
    return


def test_config_registry_freeze_prevents_override():
    """
        Test that freeze() prevents override().
    """
    registry = ConfigRegistry()
    registry.load()
    registry.freeze()
    
    try:
        registry.override("key", "value")
        raise AssertionError("Expected ConfigurationFrozenError")
    except ConfigurationFrozenError as e:
        if e.key != "key":
            errmsg = f"Expected error key 'key', got {e.key}"
            raise AssertionError(errmsg)
    
    return


def test_config_registry_freeze_prevents_clear_override():
    """
        Test that freeze() prevents clear_override().
    """
    registry = ConfigRegistry()
    registry.load()
    registry.override("key", "value")
    registry.freeze()
    
    try:
        registry.clear_override("key")
        raise AssertionError("Expected ConfigurationFrozenError")
    except ConfigurationFrozenError:
        pass
    
    return


def test_config_registry_freeze_prevents_clear_all_overrides():
    """
        Test that freeze() prevents clear_all_overrides().
    """
    registry = ConfigRegistry()
    registry.load()
    registry.override("key", "value")
    registry.freeze()
    
    try:
        registry.clear_all_overrides()
        raise AssertionError("Expected ConfigurationFrozenError")
    except ConfigurationFrozenError:
        pass
    
    return


def test_config_registry_freeze_prevents_register_source():
    """
        Test that freeze() prevents register_source().
    """
    registry = ConfigRegistry()
    registry.freeze()
    
    source = MockConfigSource({"key": "value"})
    
    try:
        registry.register_source(source)
        raise AssertionError("Expected ConfigurationFrozenError")
    except ConfigurationFrozenError:
        pass
    
    return


def test_config_registry_freeze_allows_read():
    """
        Test that freeze() still allows reading values.
    """
    schema = ConfigSchema()
    schema.define("key", str, default="value")
    
    registry = ConfigRegistry(schema=schema)
    registry.load()
    registry.freeze()
    
    # Reading should still work
    value = registry.get("key")
    if value != "value":
        errmsg = f"Expected 'value', got {value}"
        raise AssertionError(errmsg)
    
    return


# =============================================================================
# Property Tests for Configuration Freeze
# =============================================================================

def test_property_configuration_freeze():
    """
        Property 25: Configuration Freeze
        
        *For any* frozen configuration, attempting to modify values via override()
        SHALL raise ConfigurationFrozenError.
        
        **Validates: Requirements 6.7, 6.8**
        
        This test verifies that frozen configurations cannot be modified.
    """
    import random
    import string
    
    def generate_random_key():
        """Generate a random configuration key."""
        return "test." + "".join(random.choices(string.ascii_lowercase, k=6))
    
    def generate_random_value():
        """Generate a random configuration value."""
        return "".join(random.choices(string.ascii_letters + string.digits, k=10))
    
    # Run 100 iterations
    for iteration in range(100):
        # Generate random keys and values
        num_keys = random.randint(1, 5)
        initial_values = {
            generate_random_key(): generate_random_value()
            for _ in range(num_keys)
        }
        
        # Create registry with initial values
        source = MockConfigSource(initial_values)
        registry = ConfigRegistry()
        registry.register_source(source)
        registry.load()
        
        # Freeze the configuration
        registry.freeze()
        
        # Verify frozen flag
        if not registry.is_frozen:
            errmsg = f"Iteration {iteration}: Expected is_frozen=True after freeze()"
            raise AssertionError(errmsg)
        
        # Try to override each key - should raise error
        for key in initial_values.keys():
            new_value = generate_random_value()
            try:
                registry.override(key, new_value)
                errmsg = (
                    f"Iteration {iteration}: Expected ConfigurationFrozenError "
                    f"when overriding key '{key}'"
                )
                raise AssertionError(errmsg)
            except ConfigurationFrozenError as e:
                # Verify the error contains the key
                if e.key != key:
                    errmsg = (
                        f"Iteration {iteration}: Expected error key '{key}', "
                        f"got '{e.key}'"
                    )
                    raise AssertionError(errmsg)
        
        # Try to override a new key - should also raise error
        new_key = generate_random_key()
        try:
            registry.override(new_key, generate_random_value())
            errmsg = (
                f"Iteration {iteration}: Expected ConfigurationFrozenError "
                f"when overriding new key '{new_key}'"
            )
            raise AssertionError(errmsg)
        except ConfigurationFrozenError:
            pass
        
        # Verify values are unchanged
        for key, expected_value in initial_values.items():
            actual_value = registry.get(key)
            if actual_value != expected_value:
                errmsg = (
                    f"Iteration {iteration}: Value for '{key}' changed from "
                    f"'{expected_value}' to '{actual_value}' despite freeze"
                )
                raise AssertionError(errmsg)
    
    return


def test_property_freeze_prevents_all_modifications():
    """
        Property 25: Configuration Freeze (All Modifications)
        
        Verifies that freeze prevents all modification operations.
        
        **Validates: Requirements 6.7, 6.8**
    """
    import random
    import string
    
    # Run 100 iterations
    for iteration in range(100):
        # Create registry
        registry = ConfigRegistry()
        registry.load()
        
        # Add some overrides before freezing
        num_overrides = random.randint(0, 3)
        override_keys = []
        for _ in range(num_overrides):
            key = "pre." + "".join(random.choices(string.ascii_lowercase, k=5))
            registry.override(key, "value")
            override_keys.append(key)
        
        # Freeze
        registry.freeze()
        
        # Test all modification operations
        modification_operations = [
            ("override", lambda: registry.override("new.key", "value")),
            ("register_source", lambda: registry.register_source(MockConfigSource({}))),
            ("clear_all_overrides", lambda: registry.clear_all_overrides()),
            ("update", lambda: registry.update({"key": "value"})),
        ]
        
        # Add clear_override if there are overrides
        if override_keys:
            modification_operations.append(
                ("clear_override", lambda: registry.clear_override(override_keys[0]))
            )
        
        for op_name, operation in modification_operations:
            try:
                operation()
                errmsg = (
                    f"Iteration {iteration}: Expected ConfigurationFrozenError "
                    f"for operation '{op_name}'"
                )
                raise AssertionError(errmsg)
            except ConfigurationFrozenError:
                pass
    
    return


# =============================================================================
# Unit Tests for Change Notification
# =============================================================================

def test_config_registry_on_change_callback():
    """
        Test that on_change() registers a callback.
    """
    registry = ConfigRegistry()
    registry.load()
    
    events = []
    
    def callback(event):
        events.append(event)
    
    registry.on_change(callback)
    registry.override("key", "value")
    
    if len(events) != 1:
        errmsg = f"Expected 1 event, got {len(events)}"
        raise AssertionError(errmsg)
    
    event = events[0]
    if event.key != "key":
        errmsg = f"Expected event key 'key', got {event.key}"
        raise AssertionError(errmsg)
    
    if event.new_value != "value":
        errmsg = f"Expected new_value 'value', got {event.new_value}"
        raise AssertionError(errmsg)
    
    return


def test_config_registry_on_change_multiple_callbacks():
    """
        Test that multiple callbacks can be registered.
    """
    registry = ConfigRegistry()
    registry.load()
    
    events1 = []
    events2 = []
    
    registry.on_change(lambda e: events1.append(e))
    registry.on_change(lambda e: events2.append(e))
    
    registry.override("key", "value")
    
    if len(events1) != 1:
        errmsg = f"Expected 1 event in callback1, got {len(events1)}"
        raise AssertionError(errmsg)
    
    if len(events2) != 1:
        errmsg = f"Expected 1 event in callback2, got {len(events2)}"
        raise AssertionError(errmsg)
    
    return


def test_config_registry_on_change_old_value():
    """
        Test that change event contains old value.
    """
    registry = ConfigRegistry()
    source = MockConfigSource({"key": "old_value"})
    registry.register_source(source)
    registry.load()
    
    events = []
    registry.on_change(lambda e: events.append(e))
    
    registry.override("key", "new_value")
    
    if len(events) != 1:
        errmsg = f"Expected 1 event, got {len(events)}"
        raise AssertionError(errmsg)
    
    event = events[0]
    if event.old_value != "old_value":
        errmsg = f"Expected old_value 'old_value', got {event.old_value}"
        raise AssertionError(errmsg)
    
    if event.new_value != "new_value":
        errmsg = f"Expected new_value 'new_value', got {event.new_value}"
        raise AssertionError(errmsg)
    
    return


def test_config_registry_on_change_no_event_for_same_value():
    """
        Test that no event is fired when value doesn't change.
    """
    registry = ConfigRegistry()
    registry.load()
    
    events = []
    registry.on_change(lambda e: events.append(e))
    
    # Set initial value
    registry.override("key", "value")
    
    # Set same value again
    registry.override("key", "value")
    
    # Should only have 1 event (from first override)
    if len(events) != 1:
        errmsg = f"Expected 1 event (no event for same value), got {len(events)}"
        raise AssertionError(errmsg)
    
    return


def test_config_registry_remove_change_callback():
    """
        Test that remove_change_callback() removes a callback.
    """
    registry = ConfigRegistry()
    registry.load()
    
    events = []
    
    def callback(event):
        events.append(event)
    
    registry.on_change(callback)
    registry.override("key1", "value1")
    
    # Remove callback
    result = registry.remove_change_callback(callback)
    if not result:
        errmsg = "Expected remove_change_callback to return True"
        raise AssertionError(errmsg)
    
    # This should not trigger callback
    registry.override("key2", "value2")
    
    if len(events) != 1:
        errmsg = f"Expected 1 event after removal, got {len(events)}"
        raise AssertionError(errmsg)
    
    return


def test_config_registry_remove_nonexistent_callback():
    """
        Test that remove_change_callback() returns False for unknown callback.
    """
    registry = ConfigRegistry()
    
    def callback(event):
        pass
    
    result = registry.remove_change_callback(callback)
    
    if result:
        errmsg = "Expected remove_change_callback to return False for unknown callback"
        raise AssertionError(errmsg)
    
    return


def test_config_registry_callback_error_does_not_break():
    """
        Test that callback errors don't break the registry.
    """
    registry = ConfigRegistry()
    registry.load()
    
    events = []
    
    def bad_callback(event):
        raise RuntimeError("Callback error")
    
    def good_callback(event):
        events.append(event)
    
    registry.on_change(bad_callback)
    registry.on_change(good_callback)
    
    # Should not raise, and good_callback should still be called
    registry.override("key", "value")
    
    if len(events) != 1:
        errmsg = f"Expected 1 event despite bad callback, got {len(events)}"
        raise AssertionError(errmsg)
    
    return


# =============================================================================
# Property Tests for Change Notification Callbacks
# =============================================================================

def test_property_change_notification_callbacks():
    """
        Property 23: Change Notification Callbacks
        
        *For any* registered change callback and configuration change, the callback
        SHALL be invoked with a ConfigChangeEvent containing the old value, new value,
        and source.
        
        **Validates: Requirements 6.5**
        
        This test verifies that change callbacks receive correct event data.
    """
    import random
    import string
    from datetime import datetime, timedelta, timezone
    
    def generate_random_key():
        """Generate a random configuration key."""
        return "notify." + "".join(random.choices(string.ascii_lowercase, k=6))
    
    def generate_random_value():
        """Generate a random configuration value."""
        return "".join(random.choices(string.ascii_letters + string.digits, k=10))
    
    # Run 100 iterations
    for iteration in range(100):
        # Create registry with initial values
        num_keys = random.randint(1, 5)
        initial_values = {
            generate_random_key(): generate_random_value()
            for _ in range(num_keys)
        }
        
        source = MockConfigSource(initial_values)
        registry = ConfigRegistry()
        registry.register_source(source)
        registry.load()
        
        # Register callback
        events = []
        registry.on_change(lambda e: events.append(e))
        
        # Pick a random key to override
        key = random.choice(list(initial_values.keys()))
        old_value = initial_values[key]
        new_value = generate_random_value()
        
        # Record time before override
        before_time = datetime.now(timezone.utc)
        
        # Override the value
        registry.override(key, new_value)
        
        # Record time after override
        after_time = datetime.now(timezone.utc)
        
        # Verify callback was invoked
        if len(events) != 1:
            errmsg = f"Iteration {iteration}: Expected 1 event, got {len(events)}"
            raise AssertionError(errmsg)
        
        event = events[0]
        
        # Verify event key
        if event.key != key:
            errmsg = (
                f"Iteration {iteration}: Expected event key '{key}', "
                f"got '{event.key}'"
            )
            raise AssertionError(errmsg)
        
        # Verify old value
        if event.old_value != old_value:
            errmsg = (
                f"Iteration {iteration}: Expected old_value '{old_value}', "
                f"got '{event.old_value}'"
            )
            raise AssertionError(errmsg)
        
        # Verify new value
        if event.new_value != new_value:
            errmsg = (
                f"Iteration {iteration}: Expected new_value '{new_value}', "
                f"got '{event.new_value}'"
            )
            raise AssertionError(errmsg)
        
        # Verify source
        if event.source != ConfigSourceType.OVERRIDE:
            errmsg = (
                f"Iteration {iteration}: Expected source OVERRIDE, "
                f"got {event.source}"
            )
            raise AssertionError(errmsg)
        
        # Verify timestamp is reasonable (within the operation window)
        # Allow 1 second tolerance for timing
        tolerance = timedelta(seconds=1)
        if event.timestamp < before_time - tolerance or event.timestamp > after_time + tolerance:
            errmsg = (
                f"Iteration {iteration}: Event timestamp {event.timestamp} "
                f"not within expected range [{before_time}, {after_time}]"
            )
            raise AssertionError(errmsg)
    
    return


def test_property_multiple_callbacks_all_invoked():
    """
        Property 23: Change Notification Callbacks (Multiple Callbacks)
        
        Verifies that all registered callbacks are invoked on change.
        
        **Validates: Requirements 6.5**
    """
    import random
    import string
    
    # Run 100 iterations
    for iteration in range(100):
        # Create registry
        registry = ConfigRegistry()
        registry.load()
        
        # Register multiple callbacks
        num_callbacks = random.randint(1, 5)
        event_lists = [[] for _ in range(num_callbacks)]
        
        for i, event_list in enumerate(event_lists):
            registry.on_change(lambda e, el=event_list: el.append(e))
        
        # Make a change
        key = "test." + "".join(random.choices(string.ascii_lowercase, k=5))
        value = "".join(random.choices(string.ascii_letters, k=8))
        registry.override(key, value)
        
        # Verify all callbacks were invoked
        for i, event_list in enumerate(event_lists):
            if len(event_list) != 1:
                errmsg = (
                    f"Iteration {iteration}: Callback {i} expected 1 event, "
                    f"got {len(event_list)}"
                )
                raise AssertionError(errmsg)
            
            event = event_list[0]
            if event.key != key or event.new_value != value:
                errmsg = (
                    f"Iteration {iteration}: Callback {i} received incorrect event"
                )
                raise AssertionError(errmsg)
    
    return


# =============================================================================
# Unit Tests for Atomic Updates
# =============================================================================

def test_config_registry_update_atomic():
    """
        Test that update() applies multiple values atomically.
    """
    registry = ConfigRegistry()
    registry.load()
    
    updates = {
        "key1": "value1",
        "key2": "value2",
        "key3": "value3"
    }
    
    registry.update(updates)
    
    for key, expected in updates.items():
        actual = registry.get(key)
        if actual != expected:
            errmsg = f"Expected {key}='{expected}', got '{actual}'"
            raise AssertionError(errmsg)
    
    return


def test_config_registry_update_non_atomic():
    """
        Test that update() with atomic=False applies values individually.
    """
    registry = ConfigRegistry()
    registry.load()
    
    updates = {
        "key1": "value1",
        "key2": "value2"
    }
    
    registry.update(updates, atomic=False)
    
    for key, expected in updates.items():
        actual = registry.get(key)
        if actual != expected:
            errmsg = f"Expected {key}='{expected}', got '{actual}'"
            raise AssertionError(errmsg)
    
    return


def test_config_registry_update_frozen_raises():
    """
        Test that update() raises error when frozen.
    """
    registry = ConfigRegistry()
    registry.load()
    registry.freeze()
    
    try:
        registry.update({"key": "value"})
        raise AssertionError("Expected ConfigurationFrozenError")
    except ConfigurationFrozenError:
        pass
    
    return


def test_config_registry_update_atomic_rollback_on_validation_error():
    """
        Test that atomic update rolls back on validation error.
    """
    # Create schema with validation - use choices constraint for validation
    schema = ConfigSchema()
    schema.define("valid.key", str)
    schema.define("level", str, choices=["DEBUG", "INFO", "WARNING", "ERROR"])
    
    registry = ConfigRegistry(schema=schema)
    
    # Set initial valid state before load
    registry.override("level", "INFO")
    registry.load()
    
    # Try to update with invalid value (level not in choices)
    try:
        registry.update({
            "valid.key": "new_value",
            "level": "INVALID_LEVEL"  # This should fail validation
        })
        # If we get here, validation didn't fail as expected
        raise AssertionError("Expected ConfigurationValidationError")
    except ConfigurationValidationError:
        # Verify rollback - level should still be INFO
        if registry.get("level") != "INFO":
            errmsg = f"Expected level='INFO' after rollback, got {registry.get('level')}"
            raise AssertionError(errmsg)
        
        # valid.key should not have been set
        if registry.get("valid.key") == "new_value":
            errmsg = f"Expected valid.key to not be 'new_value' after rollback"
            raise AssertionError(errmsg)
    
    return


def test_config_registry_update_fires_change_events():
    """
        Test that atomic update fires change events for all updated keys.
    """
    registry = ConfigRegistry()
    registry.load()
    
    events = []
    registry.on_change(lambda e: events.append(e))
    
    updates = {
        "key1": "value1",
        "key2": "value2",
        "key3": "value3"
    }
    
    registry.update(updates)
    
    # Should have 3 events
    if len(events) != 3:
        errmsg = f"Expected 3 events, got {len(events)}"
        raise AssertionError(errmsg)
    
    # Verify all keys are represented
    event_keys = {e.key for e in events}
    expected_keys = set(updates.keys())
    if event_keys != expected_keys:
        errmsg = f"Expected event keys {expected_keys}, got {event_keys}"
        raise AssertionError(errmsg)
    
    return


# =============================================================================
# Property Tests for Atomic Updates
# =============================================================================

def test_property_atomic_updates():
    """
        Property 24: Atomic Updates
        
        *For any* configuration update involving multiple keys, either all changes
        SHALL be applied or none SHALL be applied (atomicity).
        
        **Validates: Requirements 6.6**
        
        This test verifies that atomic updates are all-or-nothing.
    """
    import random
    import string
    
    def generate_random_key():
        """Generate a random configuration key."""
        return "atomic." + "".join(random.choices(string.ascii_lowercase, k=6))
    
    def generate_random_value():
        """Generate a random configuration value."""
        return "".join(random.choices(string.ascii_letters + string.digits, k=10))
    
    # Run 100 iterations
    for iteration in range(100):
        # Create registry with initial values
        num_keys = random.randint(2, 5)
        initial_values = {
            generate_random_key(): generate_random_value()
            for _ in range(num_keys)
        }
        
        source = MockConfigSource(initial_values)
        registry = ConfigRegistry()
        registry.register_source(source)
        registry.load()
        
        # Generate new values for all keys
        new_values = {
            key: generate_random_value()
            for key in initial_values.keys()
        }
        
        # Apply atomic update
        registry.update(new_values, atomic=True)
        
        # Verify ALL values were updated
        for key, expected in new_values.items():
            actual = registry.get(key)
            if actual != expected:
                errmsg = (
                    f"Iteration {iteration}: Expected {key}='{expected}', "
                    f"got '{actual}' - atomic update incomplete"
                )
                raise AssertionError(errmsg)
    
    return


def test_property_atomic_update_all_or_nothing():
    """
        Property 24: Atomic Updates (All-or-Nothing)
        
        Verifies that failed atomic updates don't partially apply.
        
        **Validates: Requirements 6.6**
    """
    import random
    import string
    
    # Run 100 iterations
    for iteration in range(100):
        # Create schema with a choices constraint for validation
        schema = ConfigSchema()
        schema.define("level", str, choices=["DEBUG", "INFO", "WARNING", "ERROR"])
        schema.define("optional.str", str)
        
        # Create registry
        registry = ConfigRegistry(schema=schema)
        
        # Set initial valid state before load
        initial_level = random.choice(["DEBUG", "INFO", "WARNING", "ERROR"])
        registry.override("level", initial_level)
        registry.load()
        
        # Generate valid string value
        valid_str = "".join(random.choices(string.ascii_letters, k=8))
        
        # Try atomic update with invalid level value
        try:
            registry.update({
                "optional.str": valid_str,
                "level": "INVALID_LEVEL_XYZ"  # Not in choices
            }, atomic=True)
            # Should have raised validation error
            errmsg = f"Iteration {iteration}: Expected ConfigurationValidationError"
            raise AssertionError(errmsg)
        except ConfigurationValidationError:
            # Verify rollback - level should be unchanged
            actual_level = registry.get("level")
            if actual_level != initial_level:
                errmsg = (
                    f"Iteration {iteration}: Expected level='{initial_level}' "
                    f"after rollback, got '{actual_level}'"
                )
                raise AssertionError(errmsg)
            
            # optional.str should not have been set to the new value
            actual_str = registry.get("optional.str")
            if actual_str == valid_str:
                errmsg = (
                    f"Iteration {iteration}: optional.str was set to '{valid_str}' "
                    f"despite rollback - partial update occurred"
                )
                raise AssertionError(errmsg)
    
    return


def test_property_atomic_update_change_events_on_success():
    """
        Property 24: Atomic Updates (Change Events)
        
        Verifies that successful atomic updates fire change events for all keys.
        
        **Validates: Requirements 6.6**
    """
    import random
    import string
    
    # Run 100 iterations
    for iteration in range(100):
        # Create registry
        registry = ConfigRegistry()
        registry.load()
        
        # Register callback
        events = []
        registry.on_change(lambda e: events.append(e))
        
        # Generate random updates
        num_updates = random.randint(1, 5)
        updates = {
            "update." + "".join(random.choices(string.ascii_lowercase, k=5)): 
            "".join(random.choices(string.ascii_letters, k=8))
            for _ in range(num_updates)
        }
        
        # Apply atomic update
        registry.update(updates, atomic=True)
        
        # Verify we got events for all keys
        event_keys = {e.key for e in events}
        expected_keys = set(updates.keys())
        
        if event_keys != expected_keys:
            errmsg = (
                f"Iteration {iteration}: Expected events for keys {expected_keys}, "
                f"got events for {event_keys}"
            )
            raise AssertionError(errmsg)
        
        # Verify event values
        for event in events:
            expected_value = updates[event.key]
            if event.new_value != expected_value:
                errmsg = (
                    f"Iteration {iteration}: Event for '{event.key}' has "
                    f"new_value='{event.new_value}', expected '{expected_value}'"
                )
                raise AssertionError(errmsg)
    
    return


# =============================================================================
# Unit Tests for Export Functionality
# =============================================================================

def test_config_registry_export_json():
    """
        Test that export() can export configuration to JSON format.
    """
    registry = ConfigRegistry()
    source = MockConfigSource({
        "database.host": "localhost",
        "database.port": 5432,
        "logging.level": "DEBUG"
    })
    registry.register_source(source)
    registry.load()
    
    # Export to JSON
    result = registry.export("json")
    
    if result is None:
        errmsg = "Expected JSON string, got None"
        raise AssertionError(errmsg)
    
    # Parse and verify
    import json
    data = json.loads(result)
    
    if data.get("database", {}).get("host") != "localhost":
        errmsg = f"Expected database.host='localhost', got {data}"
        raise AssertionError(errmsg)
    
    if data.get("database", {}).get("port") != 5432:
        errmsg = f"Expected database.port=5432, got {data}"
        raise AssertionError(errmsg)
    
    return


def test_config_registry_export_yaml():
    """
        Test that export() can export configuration to YAML format.
    """
    try:
        import yaml
    except ImportError:
        # Skip if YAML not available
        return
    
    registry = ConfigRegistry()
    source = MockConfigSource({
        "database.host": "localhost",
        "database.port": 5432
    })
    registry.register_source(source)
    registry.load()
    
    # Export to YAML
    result = registry.export("yaml")
    
    if result is None:
        errmsg = "Expected YAML string, got None"
        raise AssertionError(errmsg)
    
    # Parse and verify
    data = yaml.safe_load(result)
    
    if data.get("database", {}).get("host") != "localhost":
        errmsg = f"Expected database.host='localhost', got {data}"
        raise AssertionError(errmsg)
    
    return


def test_config_registry_export_ini():
    """
        Test that export() can export configuration to INI format.
    """
    registry = ConfigRegistry()
    source = MockConfigSource({
        "database.host": "localhost",
        "database.port": "5432"
    })
    registry.register_source(source)
    registry.load()
    
    # Export to INI
    result = registry.export("ini")
    
    if result is None:
        errmsg = "Expected INI string, got None"
        raise AssertionError(errmsg)
    
    # Verify content contains expected sections
    if "[database]" not in result:
        errmsg = f"Expected [database] section in INI output: {result}"
        raise AssertionError(errmsg)
    
    if "host = localhost" not in result:
        errmsg = f"Expected 'host = localhost' in INI output: {result}"
        raise AssertionError(errmsg)
    
    return


def test_config_registry_export_to_file():
    """
        Test that export() can write to a file.
    """
    import tempfile
    import os
    
    registry = ConfigRegistry()
    source = MockConfigSource({"key": "value"})
    registry.register_source(source)
    registry.load()
    
    # Create temp file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        temp_path = Path(f.name)
    
    try:
        # Export to file
        result = registry.export("json", path=temp_path)
        
        # Should return None when writing to file
        if result is not None:
            errmsg = f"Expected None when writing to file, got {result}"
            raise AssertionError(errmsg)
        
        # Verify file was written
        if not temp_path.exists():
            errmsg = "Expected file to be created"
            raise AssertionError(errmsg)
        
        content = temp_path.read_text()
        if '"key"' not in content:
            errmsg = f"Expected 'key' in file content: {content}"
            raise AssertionError(errmsg)
    finally:
        if temp_path.exists():
            os.unlink(temp_path)
    
    return


def test_config_registry_export_masks_secrets():
    """
        Test that export() masks sensitive values by default.
    """
    from ccai.webworks.configuration.core import SecretValue
    
    schema = ConfigSchema()
    schema.define("api.key", str, sensitive=True)
    schema.define("api.url", str)
    
    registry = ConfigRegistry(schema=schema)
    source = MockConfigSource({
        "api.key": "secret-api-key-12345",
        "api.url": "https://api.example.com"
    })
    registry.register_source(source)
    registry.load()
    
    # Export with masking (default)
    result = registry.export("json", mask_secrets=True)
    
    if "secret-api-key-12345" in result:
        errmsg = "Expected secret to be masked in export"
        raise AssertionError(errmsg)
    
    if SecretValue.MASKED_VALUE not in result:
        errmsg = f"Expected masked value '{SecretValue.MASKED_VALUE}' in export"
        raise AssertionError(errmsg)
    
    return


def test_config_registry_export_unmasks_secrets():
    """
        Test that export() can unmask sensitive values when requested.
    """
    schema = ConfigSchema()
    schema.define("api.key", str, sensitive=True)
    
    registry = ConfigRegistry(schema=schema)
    source = MockConfigSource({"api.key": "secret-api-key-12345"})
    registry.register_source(source)
    registry.load()
    
    # Export without masking
    result = registry.export("json", mask_secrets=False)
    
    if "secret-api-key-12345" not in result:
        errmsg = "Expected secret to be visible when mask_secrets=False"
        raise AssertionError(errmsg)
    
    return


def test_config_registry_export_unsupported_format():
    """
        Test that export() raises error for unsupported format.
    """
    registry = ConfigRegistry()
    registry.load()
    
    try:
        registry.export("unsupported_format")
        raise AssertionError("Expected ConfigurationError for unsupported format")
    except ConfigurationError:
        pass
    
    return


# =============================================================================
# Property Tests for Export Round-Trip
# =============================================================================

def test_property_export_round_trip_json():
    """
        Property 26: Export Round-Trip (JSON)
        
        *For any* configuration, exporting and then importing SHALL produce
        an equivalent configuration (excluding sensitive values if masked).
        
        **Validates: Requirements 7.1**
        
        This test verifies JSON export round-trip consistency.
    """
    import random
    import string
    import json
    
    def generate_random_key():
        """Generate a random configuration key."""
        parts = random.randint(1, 3)
        return ".".join(
            "".join(random.choices(string.ascii_lowercase, k=random.randint(3, 8)))
            for _ in range(parts)
        )
    
    def generate_random_value():
        """Generate a random configuration value (string, int, or bool)."""
        value_type = random.choice(["str", "int", "bool"])
        if value_type == "str":
            return "".join(random.choices(string.ascii_letters + string.digits, k=random.randint(5, 15)))
        elif value_type == "int":
            return random.randint(0, 10000)
        else:
            return random.choice([True, False])
    
    # Run 100 iterations
    for iteration in range(100):
        # Generate random configuration
        num_keys = random.randint(1, 10)
        original_values = {
            generate_random_key(): generate_random_value()
            for _ in range(num_keys)
        }
        
        # Create registry with values
        source = MockConfigSource(original_values)
        registry = ConfigRegistry()
        registry.register_source(source)
        registry.load()
        
        # Export to JSON
        exported = registry.export("json")
        
        # Parse the exported JSON
        from ccai.webworks.configuration.sources import _flatten_dict
        parsed = json.loads(exported)
        reimported = _flatten_dict(parsed)
        
        # Verify all original values are present
        for key, expected_value in original_values.items():
            if key not in reimported:
                errmsg = (
                    f"Iteration {iteration}: Key '{key}' missing after round-trip"
                )
                raise AssertionError(errmsg)
            
            actual_value = reimported[key]
            if actual_value != expected_value:
                errmsg = (
                    f"Iteration {iteration}: Value mismatch for '{key}': "
                    f"expected {expected_value!r}, got {actual_value!r}"
                )
                raise AssertionError(errmsg)
    
    return


def test_property_export_round_trip_yaml():
    """
        Property 26: Export Round-Trip (YAML)
        
        Verifies YAML export round-trip consistency.
        
        **Validates: Requirements 7.1**
    """
    try:
        import yaml
    except ImportError:
        # Skip if YAML not available
        return
    
    import random
    import string
    
    def generate_random_key():
        """Generate a random configuration key."""
        parts = random.randint(1, 3)
        return ".".join(
            "".join(random.choices(string.ascii_lowercase, k=random.randint(3, 8)))
            for _ in range(parts)
        )
    
    def generate_random_value():
        """Generate a random configuration value."""
        value_type = random.choice(["str", "int", "bool"])
        if value_type == "str":
            return "".join(random.choices(string.ascii_letters + string.digits, k=random.randint(5, 15)))
        elif value_type == "int":
            return random.randint(0, 10000)
        else:
            return random.choice([True, False])
    
    # Run 100 iterations
    for iteration in range(100):
        # Generate random configuration
        num_keys = random.randint(1, 10)
        original_values = {
            generate_random_key(): generate_random_value()
            for _ in range(num_keys)
        }
        
        # Create registry with values
        source = MockConfigSource(original_values)
        registry = ConfigRegistry()
        registry.register_source(source)
        registry.load()
        
        # Export to YAML
        exported = registry.export("yaml")
        
        # Parse the exported YAML
        from ccai.webworks.configuration.sources import _flatten_dict
        parsed = yaml.safe_load(exported)
        reimported = _flatten_dict(parsed) if parsed else {}
        
        # Verify all original values are present
        for key, expected_value in original_values.items():
            if key not in reimported:
                errmsg = (
                    f"Iteration {iteration}: Key '{key}' missing after round-trip"
                )
                raise AssertionError(errmsg)
            
            actual_value = reimported[key]
            if actual_value != expected_value:
                errmsg = (
                    f"Iteration {iteration}: Value mismatch for '{key}': "
                    f"expected {expected_value!r}, got {actual_value!r}"
                )
                raise AssertionError(errmsg)
    
    return


def test_property_export_round_trip_ini():
    """
        Property 26: Export Round-Trip (INI)
        
        Verifies INI export round-trip consistency.
        Note: INI format converts all values to strings.
        
        **Validates: Requirements 7.1**
    """
    import random
    import string
    
    def generate_random_key():
        """Generate a random configuration key with section."""
        section = "".join(random.choices(string.ascii_lowercase, k=random.randint(3, 8)))
        key = "".join(random.choices(string.ascii_lowercase, k=random.randint(3, 8)))
        return f"{section}.{key}"
    
    def generate_random_value():
        """Generate a random string value (INI only supports strings)."""
        return "".join(random.choices(string.ascii_letters + string.digits, k=random.randint(5, 15)))
    
    # Run 100 iterations
    for iteration in range(100):
        # Generate random configuration (all string values for INI)
        num_keys = random.randint(1, 10)
        original_values = {
            generate_random_key(): generate_random_value()
            for _ in range(num_keys)
        }
        
        # Create registry with values
        source = MockConfigSource(original_values)
        registry = ConfigRegistry()
        registry.register_source(source)
        registry.load()
        
        # Export to INI
        exported = registry.export("ini")
        
        # Parse the exported INI
        from ccai.webworks.configuration.sources import IniLoader
        loader = IniLoader()
        reimported = loader.load(exported)
        
        # Verify all original values are present
        for key, expected_value in original_values.items():
            if key not in reimported:
                errmsg = (
                    f"Iteration {iteration}: Key '{key}' missing after round-trip"
                )
                raise AssertionError(errmsg)
            
            actual_value = reimported[key]
            # INI converts everything to strings
            expected_str = str(expected_value)
            if actual_value != expected_str:
                errmsg = (
                    f"Iteration {iteration}: Value mismatch for '{key}': "
                    f"expected {expected_str!r}, got {actual_value!r}"
                )
                raise AssertionError(errmsg)
    
    return


# =============================================================================
# Unit Tests for Template Export
# =============================================================================

def test_config_registry_export_template_yaml():
    """
        Test that export_template() generates a YAML template with defaults.
    """
    try:
        import yaml
    except ImportError:
        # Skip if YAML not available
        return
    
    schema = ConfigSchema()
    schema.define("database.host", str, default="localhost", description="Database hostname")
    schema.define("database.port", int, default=5432, description="Database port")
    schema.define("logging.level", str, default="INFO", choices=["DEBUG", "INFO", "WARNING", "ERROR"])
    
    registry = ConfigRegistry(schema=schema)
    
    # Export template
    result = registry.export_template("yaml")
    
    if result is None:
        errmsg = "Expected YAML template string, got None"
        raise AssertionError(errmsg)
    
    # Verify it contains comments
    if "# Database hostname" not in result:
        errmsg = f"Expected description comment in template: {result}"
        raise AssertionError(errmsg)
    
    # Verify it contains default values
    if "localhost" not in result:
        errmsg = f"Expected default value 'localhost' in template: {result}"
        raise AssertionError(errmsg)
    
    return


def test_config_registry_export_template_json():
    """
        Test that export_template() generates a JSON template.
    """
    schema = ConfigSchema()
    schema.define("api.url", str, default="https://api.example.com")
    schema.define("api.timeout", int, default=30)
    
    registry = ConfigRegistry(schema=schema)
    
    # Export template
    result = registry.export_template("json")
    
    if result is None:
        errmsg = "Expected JSON template string, got None"
        raise AssertionError(errmsg)
    
    # Parse and verify
    import json
    data = json.loads(result)
    
    if data.get("api", {}).get("url") != "https://api.example.com":
        errmsg = f"Expected api.url default in template: {data}"
        raise AssertionError(errmsg)
    
    return


def test_config_registry_export_template_ini():
    """
        Test that export_template() generates an INI template with comments.
    """
    schema = ConfigSchema()
    schema.define("server.host", str, default="0.0.0.0", description="Server bind address")
    schema.define("server.port", int, default=8080, description="Server port")
    
    registry = ConfigRegistry(schema=schema)
    
    # Export template
    result = registry.export_template("ini")
    
    if result is None:
        errmsg = "Expected INI template string, got None"
        raise AssertionError(errmsg)
    
    # Verify it contains comments
    if "; Server bind address" not in result:
        errmsg = f"Expected description comment in template: {result}"
        raise AssertionError(errmsg)
    
    # Verify it contains section
    if "[server]" not in result:
        errmsg = f"Expected [server] section in template: {result}"
        raise AssertionError(errmsg)
    
    return


def test_config_registry_export_template_toml():
    """
        Test that export_template() generates a TOML template with comments.
    """
    schema = ConfigSchema()
    schema.define("cache.enabled", bool, default=True, description="Enable caching")
    schema.define("cache.ttl", int, default=3600, description="Cache TTL in seconds")
    
    registry = ConfigRegistry(schema=schema)
    
    # Export template
    result = registry.export_template("toml")
    
    if result is None:
        errmsg = "Expected TOML template string, got None"
        raise AssertionError(errmsg)
    
    # Verify it contains comments
    if "# Enable caching" not in result:
        errmsg = f"Expected description comment in template: {result}"
        raise AssertionError(errmsg)
    
    # Verify it contains section
    if "[cache]" not in result:
        errmsg = f"Expected [cache] section in template: {result}"
        raise AssertionError(errmsg)
    
    return


def test_config_registry_export_template_masks_sensitive():
    """
        Test that export_template() masks sensitive values.
    """
    from ccai.webworks.configuration.core import SecretValue
    
    schema = ConfigSchema()
    schema.define("api.key", str, default="default-key", sensitive=True)
    schema.define("api.url", str, default="https://api.example.com")
    
    registry = ConfigRegistry(schema=schema)
    
    # Export template
    result = registry.export_template("json")
    
    # Sensitive value should be masked
    if "default-key" in result:
        errmsg = "Expected sensitive default to be masked in template"
        raise AssertionError(errmsg)
    
    if SecretValue.MASKED_VALUE not in result:
        errmsg = f"Expected masked value in template: {result}"
        raise AssertionError(errmsg)
    
    return


def test_config_registry_export_template_no_schema_raises():
    """
        Test that export_template() raises error without schema.
    """
    registry = ConfigRegistry()
    
    try:
        registry.export_template("yaml")
        raise AssertionError("Expected ConfigurationError without schema")
    except ConfigurationError:
        pass
    
    return


def test_config_registry_export_template_includes_type_info():
    """
        Test that export_template() includes type information in comments.
    """
    schema = ConfigSchema()
    schema.define("count", int, required=True, description="Item count")
    
    registry = ConfigRegistry(schema=schema)
    
    # Export YAML template (has comments)
    result = registry.export_template("yaml")
    
    # Should include type info
    if "Type: int" not in result:
        errmsg = f"Expected type info in template: {result}"
        raise AssertionError(errmsg)
    
    # Should include required info
    if "Required" not in result:
        errmsg = f"Expected 'Required' in template: {result}"
        raise AssertionError(errmsg)
    
    return


# =============================================================================
# Unit Tests for Documentation Generation
# =============================================================================

def test_config_registry_export_documentation():
    """
        Test that export_documentation() generates markdown documentation.
    """
    schema = ConfigSchema()
    schema.define("database.host", str, default="localhost", description="Database hostname")
    schema.define("database.port", int, required=True, description="Database port number")
    schema.define("logging.level", str, default="INFO", choices=["DEBUG", "INFO", "WARNING", "ERROR"])
    
    registry = ConfigRegistry(schema=schema)
    
    # Export documentation
    result = registry.export_documentation()
    
    if result is None:
        errmsg = "Expected documentation string, got None"
        raise AssertionError(errmsg)
    
    # Verify it's markdown
    if "# Configuration Documentation" not in result:
        errmsg = f"Expected markdown header in documentation: {result}"
        raise AssertionError(errmsg)
    
    return


def test_config_registry_export_documentation_includes_key_name():
    """
        Test that documentation includes key names.
    """
    schema = ConfigSchema()
    schema.define("api.url", str, default="https://api.example.com")
    schema.define("api.timeout", int, default=30)
    
    registry = ConfigRegistry(schema=schema)
    result = registry.export_documentation()
    
    if "`api.url`" not in result:
        errmsg = f"Expected key name 'api.url' in documentation: {result}"
        raise AssertionError(errmsg)
    
    if "`api.timeout`" not in result:
        errmsg = f"Expected key name 'api.timeout' in documentation: {result}"
        raise AssertionError(errmsg)
    
    return


def test_config_registry_export_documentation_includes_type():
    """
        Test that documentation includes type information.
    """
    schema = ConfigSchema()
    schema.define("count", int, default=10)
    schema.define("enabled", bool, default=True)
    schema.define("name", str, default="test")
    
    registry = ConfigRegistry(schema=schema)
    result = registry.export_documentation()
    
    if "**Type:** `int`" not in result:
        errmsg = f"Expected type 'int' in documentation: {result}"
        raise AssertionError(errmsg)
    
    if "**Type:** `bool`" not in result:
        errmsg = f"Expected type 'bool' in documentation: {result}"
        raise AssertionError(errmsg)
    
    if "**Type:** `str`" not in result:
        errmsg = f"Expected type 'str' in documentation: {result}"
        raise AssertionError(errmsg)
    
    return


def test_config_registry_export_documentation_includes_default():
    """
        Test that documentation includes default values.
    """
    schema = ConfigSchema()
    schema.define("host", str, default="localhost")
    schema.define("port", int, default=8080)
    
    registry = ConfigRegistry(schema=schema)
    result = registry.export_documentation()
    
    if "**Default:** `'localhost'`" not in result:
        errmsg = f"Expected default 'localhost' in documentation: {result}"
        raise AssertionError(errmsg)
    
    if "**Default:** `8080`" not in result:
        errmsg = f"Expected default 8080 in documentation: {result}"
        raise AssertionError(errmsg)
    
    return


def test_config_registry_export_documentation_includes_description():
    """
        Test that documentation includes descriptions.
    """
    schema = ConfigSchema()
    schema.define("timeout", int, default=30, description="Request timeout in seconds")
    
    registry = ConfigRegistry(schema=schema)
    result = registry.export_documentation()
    
    if "Request timeout in seconds" not in result:
        errmsg = f"Expected description in documentation: {result}"
        raise AssertionError(errmsg)
    
    return


def test_config_registry_export_documentation_includes_required():
    """
        Test that documentation includes required status.
    """
    schema = ConfigSchema()
    schema.define("required_key", str, required=True)
    schema.define("optional_key", str, required=False)
    
    registry = ConfigRegistry(schema=schema)
    result = registry.export_documentation()
    
    # Check for required status
    if "**Required:** Yes" not in result:
        errmsg = f"Expected 'Required: Yes' in documentation: {result}"
        raise AssertionError(errmsg)
    
    if "**Required:** No" not in result:
        errmsg = f"Expected 'Required: No' in documentation: {result}"
        raise AssertionError(errmsg)
    
    return


def test_config_registry_export_documentation_includes_choices():
    """
        Test that documentation includes choices for enum constraints.
    """
    schema = ConfigSchema()
    schema.define("level", str, choices=["DEBUG", "INFO", "WARNING", "ERROR"])
    
    registry = ConfigRegistry(schema=schema)
    result = registry.export_documentation()
    
    if "**Choices:**" not in result:
        errmsg = f"Expected 'Choices:' in documentation: {result}"
        raise AssertionError(errmsg)
    
    if "'DEBUG'" not in result:
        errmsg = f"Expected 'DEBUG' choice in documentation: {result}"
        raise AssertionError(errmsg)
    
    return


def test_config_registry_export_documentation_includes_sensitive():
    """
        Test that documentation marks sensitive values.
    """
    schema = ConfigSchema()
    schema.define("api.key", str, sensitive=True)
    
    registry = ConfigRegistry(schema=schema)
    result = registry.export_documentation()
    
    if "**Sensitive:** Yes" not in result:
        errmsg = f"Expected 'Sensitive: Yes' in documentation: {result}"
        raise AssertionError(errmsg)
    
    return


def test_config_registry_export_documentation_no_schema_raises():
    """
        Test that export_documentation() raises error without schema.
    """
    registry = ConfigRegistry()
    
    try:
        registry.export_documentation()
        raise AssertionError("Expected ConfigurationError without schema")
    except ConfigurationError:
        pass
    
    return


def test_config_registry_export_documentation_groups_by_namespace():
    """
        Test that documentation groups keys by namespace.
    """
    schema = ConfigSchema()
    schema.define("database.host", str, default="localhost")
    schema.define("database.port", int, default=5432)
    schema.define("logging.level", str, default="INFO")
    schema.define("logging.format", str, default="json")
    
    registry = ConfigRegistry(schema=schema)
    result = registry.export_documentation()
    
    # Should have namespace headers
    if "## Database" not in result:
        errmsg = f"Expected 'Database' namespace header in documentation: {result}"
        raise AssertionError(errmsg)
    
    if "## Logging" not in result:
        errmsg = f"Expected 'Logging' namespace header in documentation: {result}"
        raise AssertionError(errmsg)
    
    return


# =============================================================================
# Property Tests for Documentation Completeness
# =============================================================================

def test_property_documentation_completeness():
    """
        Property 27: Documentation Completeness
        
        *For any* configuration schema, the generated documentation SHALL include
        key name, type, default value, description, and required status for every
        defined key.
        
        **Validates: Requirements 7.2, 7.3, 7.4**
        
        This test verifies that documentation includes all required information.
    """
    import random
    import string
    
    def generate_random_key():
        """Generate a random configuration key."""
        parts = random.randint(1, 3)
        return ".".join(
            "".join(random.choices(string.ascii_lowercase, k=random.randint(3, 8)))
            for _ in range(parts)
        )
    
    def generate_random_description():
        """Generate a random description."""
        words = ["The", "A", "This", "Configuration", "Setting", "Value", "for", "of", "in"]
        return " ".join(random.choices(words, k=random.randint(3, 8)))
    
    # Run 100 iterations
    for iteration in range(100):
        # Generate random schema
        schema = ConfigSchema()
        num_keys = random.randint(1, 5)
        
        key_definitions = []
        for _ in range(num_keys):
            key = generate_random_key()
            key_type = random.choice([str, int, bool, float])
            required = random.choice([True, False])
            description = generate_random_description()
            
            # Generate appropriate default based on type
            if key_type is str:
                default = "".join(random.choices(string.ascii_letters, k=5))
            elif key_type is int:
                default = random.randint(0, 1000)
            elif key_type is bool:
                default = random.choice([True, False])
            else:
                default = round(random.uniform(0, 100), 2)
            
            schema.define(key, key_type, required=required, default=default, description=description)
            key_definitions.append({
                "key": key,
                "type": key_type,
                "required": required,
                "default": default,
                "description": description
            })
        
        # Create registry and export documentation
        registry = ConfigRegistry(schema=schema)
        doc = registry.export_documentation()
        
        # Verify each key is documented
        for defn in key_definitions:
            key = defn["key"]
            
            # Check key name is present
            if f"`{key}`" not in doc:
                errmsg = (
                    f"Iteration {iteration}: Key name '{key}' not found in documentation"
                )
                raise AssertionError(errmsg)
            
            # Check type is present
            type_name = defn["type"].__name__
            if f"`{type_name}`" not in doc:
                errmsg = (
                    f"Iteration {iteration}: Type '{type_name}' for key '{key}' "
                    f"not found in documentation"
                )
                raise AssertionError(errmsg)
            
            # Check required status is present
            required_str = "Yes" if defn["required"] else "No"
            if f"**Required:** {required_str}" not in doc:
                errmsg = (
                    f"Iteration {iteration}: Required status for key '{key}' "
                    f"not found in documentation"
                )
                raise AssertionError(errmsg)
            
            # Check description is present
            if defn["description"] not in doc:
                errmsg = (
                    f"Iteration {iteration}: Description for key '{key}' "
                    f"not found in documentation"
                )
                raise AssertionError(errmsg)
            
            # Check default is present
            default_repr = repr(defn["default"])
            if f"**Default:** `{default_repr}`" not in doc:
                errmsg = (
                    f"Iteration {iteration}: Default value for key '{key}' "
                    f"not found in documentation"
                )
                raise AssertionError(errmsg)
    
    return


def test_property_documentation_includes_choices():
    """
        Property 27: Documentation Completeness (Choices)
        
        Verifies that documentation includes choices for enum constraints.
        
        **Validates: Requirements 7.2, 7.3, 7.4**
    """
    import random
    import string
    
    # Run 100 iterations
    for iteration in range(100):
        # Generate random choices
        num_choices = random.randint(2, 5)
        choices = [
            "".join(random.choices(string.ascii_uppercase, k=random.randint(3, 8)))
            for _ in range(num_choices)
        ]
        
        # Create schema with choices
        schema = ConfigSchema()
        key = "level." + "".join(random.choices(string.ascii_lowercase, k=5))
        schema.define(key, str, choices=choices)
        
        # Export documentation
        registry = ConfigRegistry(schema=schema)
        doc = registry.export_documentation()
        
        # Verify choices are documented
        if "**Choices:**" not in doc:
            errmsg = (
                f"Iteration {iteration}: 'Choices:' not found in documentation"
            )
            raise AssertionError(errmsg)
        
        # Verify each choice is present
        for choice in choices:
            if f"'{choice}'" not in doc:
                errmsg = (
                    f"Iteration {iteration}: Choice '{choice}' not found in documentation"
                )
                raise AssertionError(errmsg)
    
    return


def test_property_documentation_marks_sensitive():
    """
        Property 27: Documentation Completeness (Sensitive)
        
        Verifies that documentation marks sensitive values.
        
        **Validates: Requirements 7.2, 7.3, 7.4**
    """
    import random
    import string
    
    # Run 100 iterations
    for iteration in range(100):
        # Create schema with sensitive key
        schema = ConfigSchema()
        key = "secret." + "".join(random.choices(string.ascii_lowercase, k=5))
        schema.define(key, str, sensitive=True)
        
        # Export documentation
        registry = ConfigRegistry(schema=schema)
        doc = registry.export_documentation()
        
        # Verify sensitive is marked
        if "**Sensitive:** Yes" not in doc:
            errmsg = (
                f"Iteration {iteration}: Sensitive marker not found in documentation"
            )
            raise AssertionError(errmsg)
    
    return


# =============================================================================
# Unit Tests for Diff Export
# =============================================================================

def test_config_registry_export_diff_empty_when_defaults():
    """
        Test that export_diff() returns empty dict when all values are defaults.
    """
    schema = ConfigSchema()
    schema.define("key1", str, default="default1")
    schema.define("key2", int, default=42)
    
    registry = ConfigRegistry(schema=schema)
    registry.load()
    
    # No overrides, should be empty diff
    diff = registry.export_diff()
    
    if len(diff) != 0:
        errmsg = f"Expected empty diff when all values are defaults, got {diff}"
        raise AssertionError(errmsg)
    
    return


def test_config_registry_export_diff_shows_overrides():
    """
        Test that export_diff() shows overridden values.
    """
    schema = ConfigSchema()
    schema.define("key1", str, default="default1")
    schema.define("key2", str, default="default2")
    
    registry = ConfigRegistry(schema=schema)
    registry.load()
    
    # Override one key
    registry.override("key1", "overridden1")
    
    diff = registry.export_diff()
    
    if "key1" not in diff:
        errmsg = f"Expected 'key1' in diff, got {diff}"
        raise AssertionError(errmsg)
    
    current, default = diff["key1"]
    if current != "overridden1":
        errmsg = f"Expected current value 'overridden1', got {current}"
        raise AssertionError(errmsg)
    
    if default != "default1":
        errmsg = f"Expected default value 'default1', got {default}"
        raise AssertionError(errmsg)
    
    # key2 should not be in diff (still at default)
    if "key2" in diff:
        errmsg = f"Expected 'key2' not in diff (still at default), got {diff}"
        raise AssertionError(errmsg)
    
    return


def test_config_registry_export_diff_shows_source_values():
    """
        Test that export_diff() shows values from sources that differ from defaults.
    """
    schema = ConfigSchema()
    schema.define("key1", str, default="default1")
    schema.define("key2", str, default="default2")
    
    # Source provides different value for key1
    source = MockConfigSource({"key1": "from_source"})
    
    registry = ConfigRegistry(schema=schema)
    registry.register_source(source)
    registry.load()
    
    diff = registry.export_diff()
    
    if "key1" not in diff:
        errmsg = f"Expected 'key1' in diff, got {diff}"
        raise AssertionError(errmsg)
    
    current, default = diff["key1"]
    if current != "from_source":
        errmsg = f"Expected current value 'from_source', got {current}"
        raise AssertionError(errmsg)
    
    return


def test_config_registry_export_diff_shows_extra_keys():
    """
        Test that export_diff() shows keys not in schema.
    """
    schema = ConfigSchema()
    schema.define("defined.key", str, default="default")
    
    # Source provides extra key not in schema
    source = MockConfigSource({
        "defined.key": "default",  # Same as default
        "extra.key": "extra_value"  # Not in schema
    })
    
    registry = ConfigRegistry(schema=schema)
    registry.register_source(source)
    registry.load()
    
    diff = registry.export_diff()
    
    # Extra key should be in diff with None as default
    if "extra.key" not in diff:
        errmsg = f"Expected 'extra.key' in diff, got {diff}"
        raise AssertionError(errmsg)
    
    current, default = diff["extra.key"]
    if current != "extra_value":
        errmsg = f"Expected current value 'extra_value', got {current}"
        raise AssertionError(errmsg)
    
    if default is not None:
        errmsg = f"Expected default None for extra key, got {default}"
        raise AssertionError(errmsg)
    
    return


def test_config_registry_export_diff_no_schema_raises():
    """
        Test that export_diff() raises error without schema.
    """
    registry = ConfigRegistry()
    registry.load()
    
    try:
        registry.export_diff()
        raise AssertionError("Expected ConfigurationError without schema")
    except ConfigurationError:
        pass
    
    return


# =============================================================================
# Property Tests for Export Diff Accuracy
# =============================================================================

def test_property_export_diff_accuracy():
    """
        Property 28: Export Diff Accuracy
        
        *For any* configuration, the exported diff SHALL contain exactly the keys
        whose values differ from their schema defaults.
        
        **Validates: Requirements 7.6**
        
        This test verifies that diff export is accurate.
    """
    import random
    import string
    
    def generate_random_key():
        """Generate a random configuration key."""
        parts = random.randint(1, 2)
        return ".".join(
            "".join(random.choices(string.ascii_lowercase, k=random.randint(3, 6)))
            for _ in range(parts)
        )
    
    def generate_random_value():
        """Generate a random string value."""
        return "".join(random.choices(string.ascii_letters + string.digits, k=random.randint(5, 10)))
    
    # Run 100 iterations
    for iteration in range(100):
        # Generate random schema with defaults
        schema = ConfigSchema()
        num_keys = random.randint(2, 6)
        
        defaults = {}
        for _ in range(num_keys):
            key = generate_random_key()
            default = generate_random_value()
            schema.define(key, str, default=default)
            defaults[key] = default
        
        # Randomly decide which keys to override
        keys_to_override = random.sample(
            list(defaults.keys()),
            k=random.randint(0, len(defaults))
        )
        
        # Create source with overridden values
        source_values = {}
        expected_diff_keys = set()
        
        for key in defaults.keys():
            if key in keys_to_override:
                # Override with different value
                new_value = generate_random_value()
                while new_value == defaults[key]:
                    new_value = generate_random_value()
                source_values[key] = new_value
                expected_diff_keys.add(key)
            else:
                # Keep default (don't add to source)
                pass
        
        # Create registry
        registry = ConfigRegistry(schema=schema)
        if source_values:
            source = MockConfigSource(source_values)
            registry.register_source(source)
        registry.load()
        
        # Get diff
        diff = registry.export_diff()
        actual_diff_keys = set(diff.keys())
        
        # Verify diff contains exactly the expected keys
        if actual_diff_keys != expected_diff_keys:
            errmsg = (
                f"Iteration {iteration}: Expected diff keys {expected_diff_keys}, "
                f"got {actual_diff_keys}"
            )
            raise AssertionError(errmsg)
        
        # Verify diff values are correct
        for key in expected_diff_keys:
            current, default = diff[key]
            expected_current = source_values[key]
            expected_default = defaults[key]
            
            if current != expected_current:
                errmsg = (
                    f"Iteration {iteration}: For key '{key}', expected current "
                    f"'{expected_current}', got '{current}'"
                )
                raise AssertionError(errmsg)
            
            if default != expected_default:
                errmsg = (
                    f"Iteration {iteration}: For key '{key}', expected default "
                    f"'{expected_default}', got '{default}'"
                )
                raise AssertionError(errmsg)
    
    return


def test_property_export_diff_excludes_unchanged():
    """
        Property 28: Export Diff Accuracy (Excludes Unchanged)
        
        Verifies that diff excludes keys that match their defaults.
        
        **Validates: Requirements 7.6**
    """
    import random
    import string
    
    # Run 100 iterations
    for iteration in range(100):
        # Create schema with multiple keys
        schema = ConfigSchema()
        num_keys = random.randint(3, 8)
        
        defaults = {}
        for i in range(num_keys):
            key = f"key{i}." + "".join(random.choices(string.ascii_lowercase, k=4))
            default = "".join(random.choices(string.ascii_letters, k=6))
            schema.define(key, str, default=default)
            defaults[key] = default
        
        # Create source that provides same values as defaults
        source = MockConfigSource(dict(defaults))
        
        registry = ConfigRegistry(schema=schema)
        registry.register_source(source)
        registry.load()
        
        # Get diff - should be empty since all values match defaults
        diff = registry.export_diff()
        
        if len(diff) != 0:
            errmsg = (
                f"Iteration {iteration}: Expected empty diff when all values "
                f"match defaults, got {diff}"
            )
            raise AssertionError(errmsg)
    
    return


def test_property_export_diff_includes_extra_keys():
    """
        Property 28: Export Diff Accuracy (Extra Keys)
        
        Verifies that diff includes keys not defined in schema.
        
        **Validates: Requirements 7.6**
    """
    import random
    import string
    
    # Run 100 iterations
    for iteration in range(100):
        # Create schema with some keys
        schema = ConfigSchema()
        schema_keys = []
        for i in range(random.randint(1, 3)):
            key = f"schema{i}." + "".join(random.choices(string.ascii_lowercase, k=4))
            schema.define(key, str, default="default")
            schema_keys.append(key)
        
        # Create source with extra keys not in schema
        source_values = {key: "default" for key in schema_keys}  # Match defaults
        
        extra_keys = []
        for i in range(random.randint(1, 3)):
            key = f"extra{i}." + "".join(random.choices(string.ascii_lowercase, k=4))
            value = "".join(random.choices(string.ascii_letters, k=6))
            source_values[key] = value
            extra_keys.append(key)
        
        registry = ConfigRegistry(schema=schema)
        source = MockConfigSource(source_values)
        registry.register_source(source)
        registry.load()
        
        # Get diff
        diff = registry.export_diff()
        
        # Extra keys should be in diff
        for key in extra_keys:
            if key not in diff:
                errmsg = (
                    f"Iteration {iteration}: Extra key '{key}' not in diff"
                )
                raise AssertionError(errmsg)
            
            current, default = diff[key]
            if default is not None:
                errmsg = (
                    f"Iteration {iteration}: Expected None default for extra key "
                    f"'{key}', got {default}"
                )
                raise AssertionError(errmsg)
    
    return


# =============================================================================
# Property Tests for Export Secret Masking
# =============================================================================

def test_property_export_secret_masking():
    """
        Property 29: Export Secret Masking
        
        *For any* export operation with mask_secrets=True (the default), sensitive
        values SHALL be masked in the output.
        
        **Validates: Requirements 7.7**
        
        This test verifies that sensitive values are masked in exports.
    """
    import random
    import string
    from ccai.webworks.configuration.core import SecretValue
    
    def generate_random_key():
        """Generate a random configuration key."""
        parts = random.randint(1, 2)
        return ".".join(
            "".join(random.choices(string.ascii_lowercase, k=random.randint(3, 6)))
            for _ in range(parts)
        )
    
    def generate_random_secret():
        """Generate a random secret value."""
        return "SECRET_" + "".join(random.choices(string.ascii_letters + string.digits, k=random.randint(10, 20)))
    
    # Run 100 iterations
    for iteration in range(100):
        # Create schema with sensitive and non-sensitive keys
        schema = ConfigSchema()
        
        sensitive_keys = []
        non_sensitive_keys = []
        source_values = {}
        
        # Add some sensitive keys
        num_sensitive = random.randint(1, 3)
        for _ in range(num_sensitive):
            key = generate_random_key()
            secret = generate_random_secret()
            schema.define(key, str, sensitive=True)
            sensitive_keys.append(key)
            source_values[key] = secret
        
        # Add some non-sensitive keys
        num_non_sensitive = random.randint(1, 3)
        for _ in range(num_non_sensitive):
            key = generate_random_key()
            value = "".join(random.choices(string.ascii_letters, k=8))
            schema.define(key, str, sensitive=False)
            non_sensitive_keys.append(key)
            source_values[key] = value
        
        # Create registry
        registry = ConfigRegistry(schema=schema)
        source = MockConfigSource(source_values)
        registry.register_source(source)
        registry.load()
        
        # Export with masking (default)
        exported = registry.export("json", mask_secrets=True)
        
        # Verify sensitive values are masked
        for key in sensitive_keys:
            secret = source_values[key]
            if secret in exported:
                errmsg = (
                    f"Iteration {iteration}: Sensitive value for '{key}' "
                    f"was not masked in export"
                )
                raise AssertionError(errmsg)
        
        # Verify masked value is present
        if SecretValue.MASKED_VALUE not in exported:
            errmsg = (
                f"Iteration {iteration}: Expected masked value "
                f"'{SecretValue.MASKED_VALUE}' in export"
            )
            raise AssertionError(errmsg)
        
        # Verify non-sensitive values are present
        for key in non_sensitive_keys:
            value = source_values[key]
            if value not in exported:
                errmsg = (
                    f"Iteration {iteration}: Non-sensitive value for '{key}' "
                    f"was incorrectly masked"
                )
                raise AssertionError(errmsg)
    
    return


def test_property_export_secret_unmasking():
    """
        Property 29: Export Secret Masking (Unmasking)
        
        Verifies that sensitive values can be unmasked when explicitly requested.
        
        **Validates: Requirements 7.7**
    """
    import random
    import string
    
    def generate_random_secret():
        """Generate a random secret value."""
        return "SECRET_" + "".join(random.choices(string.ascii_letters + string.digits, k=random.randint(10, 20)))
    
    # Run 100 iterations
    for iteration in range(100):
        # Create schema with sensitive key
        schema = ConfigSchema()
        key = "api." + "".join(random.choices(string.ascii_lowercase, k=5))
        secret = generate_random_secret()
        schema.define(key, str, sensitive=True)
        
        # Create registry
        registry = ConfigRegistry(schema=schema)
        source = MockConfigSource({key: secret})
        registry.register_source(source)
        registry.load()
        
        # Export without masking
        exported = registry.export("json", mask_secrets=False)
        
        # Verify secret is visible
        if secret not in exported:
            errmsg = (
                f"Iteration {iteration}: Secret was not visible when "
                f"mask_secrets=False"
            )
            raise AssertionError(errmsg)
    
    return


def test_property_export_secret_masking_all_formats():
    """
        Property 29: Export Secret Masking (All Formats)
        
        Verifies that secret masking works for all export formats.
        
        **Validates: Requirements 7.7**
    """
    import random
    import string
    from ccai.webworks.configuration.core import SecretValue
    
    formats_to_test = ["json", "ini"]
    
    # Add YAML if available
    try:
        import yaml
        formats_to_test.append("yaml")
    except ImportError:
        pass
    
    # Run 100 iterations
    for iteration in range(100):
        # Create schema with sensitive key
        schema = ConfigSchema()
        key = "secret." + "".join(random.choices(string.ascii_lowercase, k=5))
        secret = "SECRET_" + "".join(random.choices(string.ascii_letters, k=15))
        schema.define(key, str, sensitive=True)
        
        # Create registry
        registry = ConfigRegistry(schema=schema)
        source = MockConfigSource({key: secret})
        registry.register_source(source)
        registry.load()
        
        # Test each format
        for fmt in formats_to_test:
            exported = registry.export(fmt, mask_secrets=True)
            
            # Verify secret is masked
            if secret in exported:
                errmsg = (
                    f"Iteration {iteration}: Secret was not masked in "
                    f"{fmt} export"
                )
                raise AssertionError(errmsg)
            
            # Verify masked value is present
            if SecretValue.MASKED_VALUE not in exported:
                errmsg = (
                    f"Iteration {iteration}: Masked value not found in "
                    f"{fmt} export"
                )
                raise AssertionError(errmsg)
    
    return


# =============================================================================
# Property Test: Lazy Loading
# =============================================================================

class TrackingConfigSource(ConfigSource):
    """
        A configuration source that tracks whether load() has been called.
        
        This is used to verify that lazy loading defers source loading
        until first access.
    """
    
    def __init__(
        self,
        values: Dict[str, Any],
        source_type: ConfigSourceType = ConfigSourceType.FILE
    ):
        self._values = values
        self._source_type = source_type
        self.load_count = 0
    
    def load(self) -> Dict[str, Any]:
        self.load_count += 1
        return dict(self._values)
    
    @property
    def source_type(self) -> ConfigSourceType:
        return self._source_type


def test_property_lazy_loading():
    """
        Property 30: Lazy Loading
        
        *For any* configuration with lazy loading enabled, values SHALL only
        be loaded from sources when first accessed.
        
        **Validates: Requirements 8.3**
        
        This test verifies that:
        1. When lazy=True, calling load() does NOT trigger source loading.
        2. The first access to a value triggers the deferred source loading.
        3. After loading, values are correctly available.
        4. Subsequent accesses do not trigger additional loads.
    """
    import random
    import string
    
    def generate_random_key():
        """Generate a random configuration key."""
        parts = random.randint(1, 3)
        return ".".join(
            "".join(random.choices(string.ascii_lowercase, k=random.randint(3, 8)))
            for _ in range(parts)
        )
    
    def generate_random_value():
        """Generate a random configuration value."""
        return "".join(random.choices(string.ascii_letters + string.digits, k=random.randint(5, 15)))
    
    # Run 100 iterations with random configurations
    for iteration in range(100):
        # Generate random configuration data
        num_keys = random.randint(1, 10)
        config_data: Dict[str, Any] = {}
        for _ in range(num_keys):
            key = generate_random_key()
            config_data[key] = generate_random_value()
        
        # Pick a random source type
        source_type = random.choice([
            ConfigSourceType.FILE,
            ConfigSourceType.ENVIRONMENT,
            ConfigSourceType.SECRETS
        ])
        
        # Create a tracking source
        tracking_source = TrackingConfigSource(config_data, source_type=source_type)
        
        # Create a lazy registry
        registry = ConfigRegistry(lazy=True)
        registry.register_source(tracking_source)
        
        # Call load() - source should NOT be loaded yet
        registry.load()
        
        if tracking_source.load_count != 0:
            errmsg = (
                f"Iteration {iteration}: Source was loaded during load() "
                f"with lazy=True. load_count={tracking_source.load_count}"
            )
            raise AssertionError(errmsg)
        
        # Registry should report as loaded (it is logically loaded, just deferred)
        if not registry.is_loaded:
            errmsg = (
                f"Iteration {iteration}: Registry should report is_loaded=True "
                f"after load() even with lazy=True"
            )
            raise AssertionError(errmsg)
        
        # Pick a random key to access
        access_key = random.choice(list(config_data.keys()))
        expected_value = config_data[access_key]
        
        # First access should trigger the load
        actual_value = registry.get(access_key)
        
        if tracking_source.load_count != 1:
            errmsg = (
                f"Iteration {iteration}: Expected exactly 1 source load after "
                f"first access, got {tracking_source.load_count}"
            )
            raise AssertionError(errmsg)
        
        if actual_value != expected_value:
            errmsg = (
                f"Iteration {iteration}: Expected value '{expected_value}' "
                f"for key '{access_key}', got '{actual_value}'"
            )
            raise AssertionError(errmsg)
        
        # Verify all keys are available after first access
        for key, expected in config_data.items():
            actual = registry.get(key)
            if actual != expected:
                errmsg = (
                    f"Iteration {iteration}: After lazy load, expected "
                    f"'{expected}' for key '{key}', got '{actual}'"
                )
                raise AssertionError(errmsg)
        
        # Subsequent accesses should NOT trigger additional loads
        if tracking_source.load_count != 1:
            errmsg = (
                f"Iteration {iteration}: Expected load_count to remain 1 "
                f"after subsequent accesses, got {tracking_source.load_count}"
            )
            raise AssertionError(errmsg)
    
    return


def test_property_lazy_loading_all_access_methods():
    """
        Property 30: Lazy Loading (Access Method Variants)
        
        Verifies that lazy loading is triggered by any access method:
        get(), get_value(), keys(), and items().
        
        **Validates: Requirements 8.3**
    """
    import random
    import string
    
    access_methods = ["get", "get_value", "keys", "items"]
    
    for iteration in range(100):
        # Generate random config
        key = "test." + "".join(random.choices(string.ascii_lowercase, k=6))
        value = "".join(random.choices(string.ascii_letters, k=10))
        config_data = {key: value}
        
        # Pick a random access method for this iteration
        method_name = random.choice(access_methods)
        
        # Create tracking source and lazy registry
        tracking_source = TrackingConfigSource(config_data)
        registry = ConfigRegistry(lazy=True)
        registry.register_source(tracking_source)
        registry.load()
        
        # Verify source not loaded yet
        if tracking_source.load_count != 0:
            errmsg = (
                f"Iteration {iteration}: Source loaded before access via "
                f"{method_name}. load_count={tracking_source.load_count}"
            )
            raise AssertionError(errmsg)
        
        # Trigger access via the chosen method
        if method_name == "get":
            result = registry.get(key)
            if result != value:
                errmsg = (
                    f"Iteration {iteration}: get() returned '{result}', "
                    f"expected '{value}'"
                )
                raise AssertionError(errmsg)
        elif method_name == "get_value":
            result = registry.get_value(key)
            if result is None or result.value != value:
                errmsg = (
                    f"Iteration {iteration}: get_value() returned unexpected "
                    f"result for key '{key}'"
                )
                raise AssertionError(errmsg)
        elif method_name == "keys":
            result = registry.keys()
            if key not in result:
                errmsg = (
                    f"Iteration {iteration}: keys() did not include '{key}'"
                )
                raise AssertionError(errmsg)
        elif method_name == "items":
            result = registry.items()
            found = any(k == key and v == value for k, v in result)
            if not found:
                errmsg = (
                    f"Iteration {iteration}: items() did not include "
                    f"('{key}', '{value}')"
                )
                raise AssertionError(errmsg)
        
        # Verify source was loaded exactly once
        if tracking_source.load_count != 1:
            errmsg = (
                f"Iteration {iteration}: Expected 1 load after {method_name}(), "
                f"got {tracking_source.load_count}"
            )
            raise AssertionError(errmsg)
    
    return


def test_property_lazy_vs_eager_equivalence():
    """
        Property 30: Lazy Loading (Equivalence)
        
        Verifies that lazy loading produces the same results as eager loading
        for any configuration.
        
        **Validates: Requirements 8.3**
    """
    import random
    import string
    
    for iteration in range(100):
        # Generate random configuration
        num_keys = random.randint(1, 8)
        config_data: Dict[str, Any] = {}
        for _ in range(num_keys):
            key = ".".join(
                "".join(random.choices(string.ascii_lowercase, k=random.randint(3, 6)))
                for _ in range(random.randint(1, 3))
            )
            config_data[key] = "".join(
                random.choices(string.ascii_letters + string.digits, k=random.randint(3, 12))
            )
        
        # Create eager registry
        eager_source = MockConfigSource(config_data)
        eager_registry = ConfigRegistry()
        eager_registry.register_source(eager_source)
        eager_registry.load()
        
        # Create lazy registry with same data
        lazy_source = MockConfigSource(dict(config_data))
        lazy_registry = ConfigRegistry(lazy=True)
        lazy_registry.register_source(lazy_source)
        lazy_registry.load()
        
        # Compare results for all keys
        for key in config_data:
            eager_val = eager_registry.get(key)
            lazy_val = lazy_registry.get(key)
            
            if eager_val != lazy_val:
                errmsg = (
                    f"Iteration {iteration}: Lazy and eager differ for key "
                    f"'{key}': eager='{eager_val}', lazy='{lazy_val}'"
                )
                raise AssertionError(errmsg)
        
        # Compare keys lists
        eager_keys = sorted(eager_registry.keys())
        lazy_keys = sorted(lazy_registry.keys())
        
        if eager_keys != lazy_keys:
            errmsg = (
                f"Iteration {iteration}: Key lists differ: "
                f"eager={eager_keys}, lazy={lazy_keys}"
            )
            raise AssertionError(errmsg)
    
    return
