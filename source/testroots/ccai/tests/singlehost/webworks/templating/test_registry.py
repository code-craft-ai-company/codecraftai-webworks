"""
    Tests for the TemplateEngineRegistry class.
    
    This module tests the TemplateEngineRegistry including:
    - Engine registration and retrieval
    - Engine instance creation
    - Default engine management
    - Engine listing and checking
    - Error handling for unregistered engines
"""

from typing import Any, Callable, Dict

from ccai.webworks.templating.engine import TemplateEngine
from ccai.webworks.templating.exceptions import TemplateEngineNotFoundError
from ccai.webworks.templating.registry import TemplateEngineRegistry


# =============================================================================
# Mock Engine Classes for Testing
# =============================================================================

class MockEngine(TemplateEngine):
    """
        Mock template engine for testing registry functionality.
    """
    
    def __init__(self, **kwargs):
        """
            Construct a MockEngine.
            
            :param kwargs: Configuration options.
        """
        self.config = kwargs
        return
    
    def render(
        self,
        template_name: str,
        context: Dict[str, Any]
    ) -> str:
        """
            Mock render implementation.
        """
        return f"MockEngine: {template_name}"
    
    def render_string(
        self,
        template_source: str,
        context: Dict[str, Any]
    ) -> str:
        """
            Mock render_string implementation.
        """
        return f"MockEngine: {template_source}"
    
    def add_filter(
        self,
        name: str,
        func: Callable[..., Any]
    ) -> None:
        """
            Mock add_filter implementation.
        """
        return
    
    def add_global(
        self,
        name: str,
        value: Any
    ) -> None:
        """
            Mock add_global implementation.
        """
        return
    
    def clear_cache(self) -> None:
        """
            Mock clear_cache implementation.
        """
        return


class AnotherMockEngine(TemplateEngine):
    """
        Another mock template engine for testing multiple registrations.
    """
    
    def __init__(self, **kwargs):
        """
            Construct an AnotherMockEngine.
        """
        self.config = kwargs
        return
    
    def render(
        self,
        template_name: str,
        context: Dict[str, Any]
    ) -> str:
        """
            Mock render implementation.
        """
        return f"AnotherMockEngine: {template_name}"
    
    def render_string(
        self,
        template_source: str,
        context: Dict[str, Any]
    ) -> str:
        """
            Mock render_string implementation.
        """
        return f"AnotherMockEngine: {template_source}"
    
    def add_filter(
        self,
        name: str,
        func: Callable[..., Any]
    ) -> None:
        """
            Mock add_filter implementation.
        """
        return
    
    def add_global(
        self,
        name: str,
        value: Any
    ) -> None:
        """
            Mock add_global implementation.
        """
        return
    
    def clear_cache(self) -> None:
        """
            Mock clear_cache implementation.
        """
        return


# =============================================================================
# Test Fixtures / Setup
# =============================================================================

def _setup_clean_registry():
    """
        Clear the registry and reset default for clean test state.
    """
    TemplateEngineRegistry.clear()
    TemplateEngineRegistry._default_engine = "jinja2"
    return


# =============================================================================
# register() Method Tests
# =============================================================================

def test_register_adds_engine_to_registry():
    """
        Test that register() adds an engine class to the registry.
    """
    _setup_clean_registry()
    
    TemplateEngineRegistry.register("mock", MockEngine)
    
    if "mock" not in TemplateEngineRegistry._engines:
        raise AssertionError("Engine should be registered")
    
    if TemplateEngineRegistry._engines["mock"] is not MockEngine:
        raise AssertionError("Engine class should be stored correctly")
    
    return


def test_register_multiple_engines():
    """
        Test that register() can register multiple engines.
    """
    _setup_clean_registry()
    
    TemplateEngineRegistry.register("mock1", MockEngine)
    TemplateEngineRegistry.register("mock2", AnotherMockEngine)
    
    if len(TemplateEngineRegistry._engines) != 2:
        raise AssertionError(f"Expected 2 engines, got {len(TemplateEngineRegistry._engines)}")
    
    if "mock1" not in TemplateEngineRegistry._engines:
        raise AssertionError("mock1 should be registered")
    
    if "mock2" not in TemplateEngineRegistry._engines:
        raise AssertionError("mock2 should be registered")
    
    return


def test_register_replaces_existing_engine():
    """
        Test that register() replaces an existing engine with the same name.
    """
    _setup_clean_registry()
    
    TemplateEngineRegistry.register("mock", MockEngine)
    TemplateEngineRegistry.register("mock", AnotherMockEngine)
    
    if TemplateEngineRegistry._engines["mock"] is not AnotherMockEngine:
        raise AssertionError("Engine should be replaced")
    
    return


def test_register_with_various_names():
    """
        Test that register() accepts various engine names.
    """
    _setup_clean_registry()
    
    TemplateEngineRegistry.register("jinja2", MockEngine)
    TemplateEngineRegistry.register("mako", MockEngine)
    TemplateEngineRegistry.register("custom-engine", MockEngine)
    TemplateEngineRegistry.register("engine_v2", MockEngine)
    
    if len(TemplateEngineRegistry._engines) != 4:
        raise AssertionError(f"Expected 4 engines, got {len(TemplateEngineRegistry._engines)}")
    
    return


# =============================================================================
# get() Method Tests
# =============================================================================

def test_get_returns_registered_engine_class():
    """
        Test that get() returns the registered engine class.
    """
    _setup_clean_registry()
    
    TemplateEngineRegistry.register("mock", MockEngine)
    
    engine_class = TemplateEngineRegistry.get("mock")
    
    if engine_class is not MockEngine:
        raise AssertionError("get() should return the registered class")
    
    return


def test_get_raises_error_for_unregistered_engine():
    """
        Test that get() raises TemplateEngineNotFoundError for unregistered engine.
    """
    _setup_clean_registry()
    
    try:
        TemplateEngineRegistry.get("nonexistent")
        raise AssertionError("Should raise TemplateEngineNotFoundError")
    except TemplateEngineNotFoundError as exc:
        if exc.engine_name != "nonexistent":
            raise AssertionError(f"Expected engine_name 'nonexistent', got '{exc.engine_name}'")
    
    return


def test_get_error_includes_available_engines():
    """
        Test that TemplateEngineNotFoundError includes available engines.
    """
    _setup_clean_registry()
    
    TemplateEngineRegistry.register("mock1", MockEngine)
    TemplateEngineRegistry.register("mock2", AnotherMockEngine)
    
    try:
        TemplateEngineRegistry.get("nonexistent")
        raise AssertionError("Should raise TemplateEngineNotFoundError")
    except TemplateEngineNotFoundError as exc:
        if "mock1" not in exc.available_engines:
            raise AssertionError("Available engines should include mock1")
        if "mock2" not in exc.available_engines:
            raise AssertionError("Available engines should include mock2")
    
    return


def test_get_error_message_contains_engine_name():
    """
        Test that error message contains the requested engine name.
    """
    _setup_clean_registry()
    
    try:
        TemplateEngineRegistry.get("unknown_engine")
        raise AssertionError("Should raise TemplateEngineNotFoundError")
    except TemplateEngineNotFoundError as exc:
        if "unknown_engine" not in str(exc):
            raise AssertionError("Error message should contain engine name")
    
    return


# =============================================================================
# create() Method Tests
# =============================================================================

def test_create_returns_engine_instance():
    """
        Test that create() returns an instance of the registered engine.
    """
    _setup_clean_registry()
    
    TemplateEngineRegistry.register("mock", MockEngine)
    
    engine = TemplateEngineRegistry.create("mock")
    
    if not isinstance(engine, MockEngine):
        raise AssertionError(f"Expected MockEngine instance, got {type(engine)}")
    
    return


def test_create_passes_kwargs_to_constructor():
    """
        Test that create() passes keyword arguments to the engine constructor.
    """
    _setup_clean_registry()
    
    TemplateEngineRegistry.register("mock", MockEngine)
    
    engine = TemplateEngineRegistry.create(
        "mock",
        template_dirs=["/templates"],
        auto_escape=True,
        cache_size=100
    )
    
    if engine.config.get("template_dirs") != ["/templates"]:
        raise AssertionError("template_dirs should be passed to constructor")
    
    if engine.config.get("auto_escape") is not True:
        raise AssertionError("auto_escape should be passed to constructor")
    
    if engine.config.get("cache_size") != 100:
        raise AssertionError("cache_size should be passed to constructor")
    
    return


def test_create_raises_error_for_unregistered_engine():
    """
        Test that create() raises TemplateEngineNotFoundError for unregistered engine.
    """
    _setup_clean_registry()
    
    try:
        TemplateEngineRegistry.create("nonexistent")
        raise AssertionError("Should raise TemplateEngineNotFoundError")
    except TemplateEngineNotFoundError as exc:
        if exc.engine_name != "nonexistent":
            raise AssertionError(f"Expected engine_name 'nonexistent', got '{exc.engine_name}'")
    
    return


def test_create_returns_new_instance_each_time():
    """
        Test that create() returns a new instance on each call.
    """
    _setup_clean_registry()
    
    TemplateEngineRegistry.register("mock", MockEngine)
    
    engine1 = TemplateEngineRegistry.create("mock")
    engine2 = TemplateEngineRegistry.create("mock")
    
    if engine1 is engine2:
        raise AssertionError("create() should return new instances")
    
    return


def test_create_instance_is_template_engine():
    """
        Test that created instance is a TemplateEngine subclass.
    """
    _setup_clean_registry()
    
    TemplateEngineRegistry.register("mock", MockEngine)
    
    engine = TemplateEngineRegistry.create("mock")
    
    if not isinstance(engine, TemplateEngine):
        raise AssertionError("Created instance should be a TemplateEngine")
    
    return


# =============================================================================
# set_default() Method Tests
# =============================================================================

def test_set_default_changes_default_engine():
    """
        Test that set_default() changes the default engine.
    """
    _setup_clean_registry()
    
    TemplateEngineRegistry.register("mock", MockEngine)
    
    TemplateEngineRegistry.set_default("mock")
    
    if TemplateEngineRegistry._default_engine != "mock":
        raise AssertionError("Default engine should be changed to 'mock'")
    
    return


def test_set_default_raises_error_for_unregistered_engine():
    """
        Test that set_default() raises error for unregistered engine.
    """
    _setup_clean_registry()
    
    try:
        TemplateEngineRegistry.set_default("nonexistent")
        raise AssertionError("Should raise TemplateEngineNotFoundError")
    except TemplateEngineNotFoundError as exc:
        if exc.engine_name != "nonexistent":
            raise AssertionError(f"Expected engine_name 'nonexistent', got '{exc.engine_name}'")
    
    return


def test_set_default_can_be_changed_multiple_times():
    """
        Test that set_default() can be called multiple times.
    """
    _setup_clean_registry()
    
    TemplateEngineRegistry.register("mock1", MockEngine)
    TemplateEngineRegistry.register("mock2", AnotherMockEngine)
    
    TemplateEngineRegistry.set_default("mock1")
    if TemplateEngineRegistry._default_engine != "mock1":
        raise AssertionError("Default should be mock1")
    
    TemplateEngineRegistry.set_default("mock2")
    if TemplateEngineRegistry._default_engine != "mock2":
        raise AssertionError("Default should be mock2")
    
    return


# =============================================================================
# list_engines() Method Tests
# =============================================================================

def test_list_engines_returns_empty_list_when_no_engines():
    """
        Test that list_engines() returns empty list when no engines registered.
    """
    _setup_clean_registry()
    
    engines = TemplateEngineRegistry.list_engines()
    
    if engines != []:
        raise AssertionError(f"Expected empty list, got {engines}")
    
    return


def test_list_engines_returns_registered_engine_names():
    """
        Test that list_engines() returns all registered engine names.
    """
    _setup_clean_registry()
    
    TemplateEngineRegistry.register("mock1", MockEngine)
    TemplateEngineRegistry.register("mock2", AnotherMockEngine)
    
    engines = TemplateEngineRegistry.list_engines()
    
    if len(engines) != 2:
        raise AssertionError(f"Expected 2 engines, got {len(engines)}")
    
    if "mock1" not in engines:
        raise AssertionError("mock1 should be in list")
    
    if "mock2" not in engines:
        raise AssertionError("mock2 should be in list")
    
    return


def test_list_engines_returns_list_type():
    """
        Test that list_engines() returns a list.
    """
    _setup_clean_registry()
    
    TemplateEngineRegistry.register("mock", MockEngine)
    
    engines = TemplateEngineRegistry.list_engines()
    
    if not isinstance(engines, list):
        raise AssertionError(f"Expected list, got {type(engines)}")
    
    return


# =============================================================================
# get_default() Method Tests
# =============================================================================

def test_get_default_returns_default_engine_name():
    """
        Test that get_default() returns the default engine name.
    """
    _setup_clean_registry()
    
    default = TemplateEngineRegistry.get_default()
    
    if default != "jinja2":
        raise AssertionError(f"Expected 'jinja2', got '{default}'")
    
    return


def test_get_default_reflects_set_default():
    """
        Test that get_default() reflects changes from set_default().
    """
    _setup_clean_registry()
    
    TemplateEngineRegistry.register("mock", MockEngine)
    TemplateEngineRegistry.set_default("mock")
    
    default = TemplateEngineRegistry.get_default()
    
    if default != "mock":
        raise AssertionError(f"Expected 'mock', got '{default}'")
    
    return


# =============================================================================
# is_registered() Method Tests
# =============================================================================

def test_is_registered_returns_true_for_registered_engine():
    """
        Test that is_registered() returns True for registered engine.
    """
    _setup_clean_registry()
    
    TemplateEngineRegistry.register("mock", MockEngine)
    
    result = TemplateEngineRegistry.is_registered("mock")
    
    if result is not True:
        raise AssertionError("is_registered should return True for registered engine")
    
    return


def test_is_registered_returns_false_for_unregistered_engine():
    """
        Test that is_registered() returns False for unregistered engine.
    """
    _setup_clean_registry()
    
    result = TemplateEngineRegistry.is_registered("nonexistent")
    
    if result is not False:
        raise AssertionError("is_registered should return False for unregistered engine")
    
    return


# =============================================================================
# unregister() Method Tests
# =============================================================================

def test_unregister_removes_engine():
    """
        Test that unregister() removes a registered engine.
    """
    _setup_clean_registry()
    
    TemplateEngineRegistry.register("mock", MockEngine)
    TemplateEngineRegistry.unregister("mock")
    
    if "mock" in TemplateEngineRegistry._engines:
        raise AssertionError("Engine should be removed")
    
    return


def test_unregister_does_nothing_for_unregistered_engine():
    """
        Test that unregister() does nothing for unregistered engine.
    """
    _setup_clean_registry()
    
    # Should not raise an error
    TemplateEngineRegistry.unregister("nonexistent")
    
    return


# =============================================================================
# clear() Method Tests
# =============================================================================

def test_clear_removes_all_engines():
    """
        Test that clear() removes all registered engines.
    """
    _setup_clean_registry()
    
    TemplateEngineRegistry.register("mock1", MockEngine)
    TemplateEngineRegistry.register("mock2", AnotherMockEngine)
    
    TemplateEngineRegistry.clear()
    
    if len(TemplateEngineRegistry._engines) != 0:
        raise AssertionError("All engines should be removed")
    
    return


def test_clear_can_be_called_on_empty_registry():
    """
        Test that clear() can be called on empty registry.
    """
    _setup_clean_registry()
    
    # Should not raise an error
    TemplateEngineRegistry.clear()
    
    if len(TemplateEngineRegistry._engines) != 0:
        raise AssertionError("Registry should remain empty")
    
    return


# =============================================================================
# TemplateEngineNotFoundError Tests
# =============================================================================

def test_template_engine_not_found_error_has_engine_name():
    """
        Test that TemplateEngineNotFoundError has engine_name attribute.
    """
    exc = TemplateEngineNotFoundError("test_engine")
    
    if exc.engine_name != "test_engine":
        raise AssertionError(f"Expected 'test_engine', got '{exc.engine_name}'")
    
    return


def test_template_engine_not_found_error_has_available_engines():
    """
        Test that TemplateEngineNotFoundError has available_engines attribute.
    """
    exc = TemplateEngineNotFoundError("test_engine", ["jinja2", "mako"])
    
    if exc.available_engines != ["jinja2", "mako"]:
        raise AssertionError(f"Expected ['jinja2', 'mako'], got {exc.available_engines}")
    
    return


def test_template_engine_not_found_error_message_format():
    """
        Test that TemplateEngineNotFoundError has proper message format.
    """
    exc = TemplateEngineNotFoundError("unknown", ["jinja2", "mako"])
    
    message = str(exc)
    
    if "unknown" not in message:
        raise AssertionError("Message should contain engine name")
    
    if "jinja2" not in message or "mako" not in message:
        raise AssertionError("Message should contain available engines")
    
    return


def test_template_engine_not_found_error_empty_available():
    """
        Test TemplateEngineNotFoundError with no available engines.
    """
    exc = TemplateEngineNotFoundError("unknown", [])
    
    message = str(exc)
    
    if "unknown" not in message:
        raise AssertionError("Message should contain engine name")
    
    if "No engines" not in message:
        raise AssertionError("Message should indicate no engines registered")
    
    return


def test_template_engine_not_found_error_default_available():
    """
        Test TemplateEngineNotFoundError with default available_engines.
    """
    exc = TemplateEngineNotFoundError("unknown")
    
    if exc.available_engines != []:
        raise AssertionError("Default available_engines should be empty list")
    
    return


# =============================================================================
# Property-Based Tests
# =============================================================================

import random
import string


def _generate_random_engine_name(length: int = 8) -> str:
    """
        Generate a random engine name for property testing.
        
        :param length: Length of the random name.
        
        :returns: Random engine name string.
    """
    chars = string.ascii_lowercase + string.digits + "_-"
    return "".join(random.choice(chars) for _ in range(length))


def _create_mock_engine_class(class_id: int) -> type:
    """
        Create a unique mock engine class with an identifier.
        
        Each class has a unique class_id attribute to distinguish it
        from other dynamically created classes.
        
        :param class_id: Unique identifier for this class.
        
        :returns: A new TemplateEngine subclass.
    """
    class DynamicMockEngine(TemplateEngine):
        """
            Dynamically created mock engine for property testing.
        """
        
        engine_class_id = class_id
        
        def __init__(self, **kwargs):
            self.config = kwargs
            return
        
        def render(
            self,
            template_name: str,
            context: Dict[str, Any]
        ) -> str:
            return f"DynamicMockEngine-{class_id}: {template_name}"
        
        def render_string(
            self,
            template_source: str,
            context: Dict[str, Any]
        ) -> str:
            return f"DynamicMockEngine-{class_id}: {template_source}"
        
        def add_filter(
            self,
            name: str,
            func: Callable[..., Any]
        ) -> None:
            return
        
        def add_global(
            self,
            name: str,
            value: Any
        ) -> None:
            return
        
        def clear_cache(self) -> None:
            return
    
    return DynamicMockEngine


def test_property_engine_registration_idempotence():
    """
        Property test for engine registration idempotence.
        
        **Property 8: Engine Registration Idempotence**
        
        *For any* template engine registered multiple times with the same name,
        only the most recent registration SHALL be active, and creating an
        engine by name SHALL return an instance of the most recently registered
        class.
        
        **Validates: Requirements 1.2**
        
        This property test verifies that:
        1. When an engine is registered multiple times with the same name,
           only the last registration is active
        2. Creating an engine by name returns an instance of the most
           recently registered class
        3. This holds for any sequence of registrations with the same name
        
        Test strategy:
        - Generate random engine names
        - Register multiple different engine classes with the same name
        - Verify that get() returns the most recently registered class
        - Verify that create() returns an instance of the most recently
          registered class
    """
    iterations = 100
    
    for iteration in range(iterations):
        _setup_clean_registry()
        
        # Generate a random engine name
        engine_name = _generate_random_engine_name()
        
        # Generate a random number of registrations (2 to 10)
        num_registrations = random.randint(2, 10)
        
        # Create unique engine classes for each registration
        engine_classes = []
        for i in range(num_registrations):
            engine_class = _create_mock_engine_class(class_id=i)
            engine_classes.append(engine_class)
        
        # Register all engine classes with the same name
        for engine_class in engine_classes:
            TemplateEngineRegistry.register(engine_name, engine_class)
        
        # The last registered class should be the active one
        expected_class = engine_classes[-1]
        expected_class_id = num_registrations - 1
        
        # Verify get() returns the most recently registered class
        retrieved_class = TemplateEngineRegistry.get(engine_name)
        
        if retrieved_class is not expected_class:
            raise AssertionError(
                f"Iteration {iteration}: get() should return the most recently "
                f"registered class. Expected class with id {expected_class_id}, "
                f"but got class with id {getattr(retrieved_class, 'engine_class_id', 'unknown')}"
            )
        
        # Verify create() returns an instance of the most recently registered class
        engine_instance = TemplateEngineRegistry.create(engine_name)
        
        if not isinstance(engine_instance, expected_class):
            raise AssertionError(
                f"Iteration {iteration}: create() should return an instance of "
                f"the most recently registered class. Expected instance of class "
                f"with id {expected_class_id}, but got instance of class with id "
                f"{getattr(type(engine_instance), 'engine_class_id', 'unknown')}"
            )
        
        # Verify the instance has the correct class_id attribute
        if getattr(type(engine_instance), 'engine_class_id', None) != expected_class_id:
            raise AssertionError(
                f"Iteration {iteration}: Instance class_id should be {expected_class_id}, "
                f"but got {getattr(type(engine_instance), 'engine_class_id', 'unknown')}"
            )
        
        # Verify only one engine is registered with this name
        if TemplateEngineRegistry._engines.get(engine_name) is not expected_class:
            raise AssertionError(
                f"Iteration {iteration}: Registry should contain only the most "
                f"recently registered class for name '{engine_name}'"
            )
    
    return


def test_property_engine_registration_idempotence_with_interleaved_names():
    """
        Property test for engine registration idempotence with interleaved names.
        
        **Property 8: Engine Registration Idempotence** (extended)
        
        This test extends the basic idempotence property to verify that
        registrations with different names do not interfere with each other.
        
        **Validates: Requirements 1.2**
        
        Test strategy:
        - Generate multiple random engine names
        - Register multiple classes for each name in an interleaved fashion
        - Verify that each name maps to its most recently registered class
    """
    iterations = 100
    
    for iteration in range(iterations):
        _setup_clean_registry()
        
        # Generate 2-5 different engine names
        num_names = random.randint(2, 5)
        engine_names = [_generate_random_engine_name() for _ in range(num_names)]
        
        # Ensure names are unique
        engine_names = list(set(engine_names))
        if len(engine_names) < 2:
            continue  # Skip if we didn't get enough unique names
        
        # Track the last registered class for each name
        last_registered = {}
        class_counter = 0
        
        # Perform random interleaved registrations
        num_total_registrations = random.randint(len(engine_names) * 2, len(engine_names) * 5)
        
        for _ in range(num_total_registrations):
            # Pick a random name to register
            name = random.choice(engine_names)
            
            # Create a new unique class
            engine_class = _create_mock_engine_class(class_id=class_counter)
            class_counter += 1
            
            # Register the class
            TemplateEngineRegistry.register(name, engine_class)
            
            # Track the last registered class for this name
            last_registered[name] = engine_class
        
        # Verify each name maps to its most recently registered class
        for name, expected_class in last_registered.items():
            retrieved_class = TemplateEngineRegistry.get(name)
            
            if retrieved_class is not expected_class:
                raise AssertionError(
                    f"Iteration {iteration}: For name '{name}', get() should return "
                    f"the most recently registered class with id "
                    f"{getattr(expected_class, 'engine_class_id', 'unknown')}, "
                    f"but got class with id "
                    f"{getattr(retrieved_class, 'engine_class_id', 'unknown')}"
                )
            
            # Verify create() returns correct instance
            engine_instance = TemplateEngineRegistry.create(name)
            
            if not isinstance(engine_instance, expected_class):
                raise AssertionError(
                    f"Iteration {iteration}: For name '{name}', create() should "
                    f"return an instance of the most recently registered class"
                )
    
    return


def test_property_engine_registration_idempotence_preserves_functionality():
    """
        Property test verifying that the most recently registered engine
        is fully functional after multiple registrations.
        
        **Property 8: Engine Registration Idempotence** (functionality)
        
        This test verifies that after multiple registrations, the active
        engine can be used for rendering operations.
        
        **Validates: Requirements 1.2**
        
        Test strategy:
        - Register multiple engine classes with the same name
        - Create an instance of the engine
        - Verify the instance can perform rendering operations
        - Verify the rendering output matches the expected class behavior
    """
    iterations = 100
    
    for iteration in range(iterations):
        _setup_clean_registry()
        
        engine_name = _generate_random_engine_name()
        
        # Register multiple classes
        num_registrations = random.randint(2, 8)
        
        for i in range(num_registrations):
            engine_class = _create_mock_engine_class(class_id=i)
            TemplateEngineRegistry.register(engine_name, engine_class)
        
        # The last class_id should be num_registrations - 1
        expected_class_id = num_registrations - 1
        
        # Create an instance
        engine = TemplateEngineRegistry.create(engine_name)
        
        # Verify render() works and produces output from the correct class
        template_name = f"test_template_{iteration}.html"
        output = engine.render(template_name, {})
        
        expected_output = f"DynamicMockEngine-{expected_class_id}: {template_name}"
        
        if output != expected_output:
            raise AssertionError(
                f"Iteration {iteration}: render() output should be from the most "
                f"recently registered class. Expected '{expected_output}', "
                f"but got '{output}'"
            )
        
        # Verify render_string() works and produces output from the correct class
        template_source = f"Hello {{ name }} - iteration {iteration}"
        output = engine.render_string(template_source, {})
        
        expected_output = f"DynamicMockEngine-{expected_class_id}: {template_source}"
        
        if output != expected_output:
            raise AssertionError(
                f"Iteration {iteration}: render_string() output should be from "
                f"the most recently registered class. Expected '{expected_output}', "
                f"but got '{output}'"
            )
    
    return
