"""
    Tests for the ComponentRegistrationHooks class.

    This module contains unit tests and property-based tests for the
    ComponentRegistrationHooks class including hook name constants,
    component registration, interface validation, and retrieval of
    registered components through the standard framework APIs.
"""

import random
import string

from typing import Any, List

from automojo.webworks.extensibility.datastructures import HookPriority
from automojo.webworks.extensibility.exceptions import ExtensionPointError
from automojo.webworks.extensibility.hookmanager import HookManager
from automojo.webworks.extensibility.componenthooks import (
    COMPONENT_REGISTRATION_HOOKS,
    COMPONENT_REQUIRED_METHODS,
    REGISTER_AUTH_PROVIDER,
    REGISTER_CLI_COMMAND,
    REGISTER_ERROR_HANDLER,
    REGISTER_MIDDLEWARE,
    REGISTER_SERIALIZER,
    REGISTER_TEMPLATE_ENGINE,
    ComponentRegistrationHooks,
    ComponentValidator,
)


# =============================================================================
# Test Helpers - Component Stubs
# =============================================================================

class _ValidMiddleware:
    """A valid middleware component with required methods."""

    def process_request(self, request: Any) -> Any:
        return request

    def process_response(self, response: Any) -> Any:
        return response


class _ValidAuthProvider:
    """A valid auth provider component with required methods."""

    def authenticate(self, credentials: Any) -> Any:
        return True


class _ValidSerializer:
    """A valid serializer component with required methods."""

    def serialize(self, data: Any) -> str:
        return str(data)

    def deserialize(self, data: str) -> Any:
        return data


class _ValidTemplateEngine:
    """A valid template engine component with required methods."""

    def render(self, template: str, context: Any) -> str:
        return template


class _ValidErrorHandler:
    """A valid error handler component with required methods."""

    def handle_error(self, error: Exception) -> Any:
        return None


class _ValidCliCommand:
    """A valid CLI command component with required methods."""

    def execute(self, args: Any) -> int:
        return 0


class _InvalidComponent:
    """A component that does not implement any required interface."""
    pass


class _PartialMiddleware:
    """A middleware component missing the process_response method."""

    def process_request(self, request: Any) -> Any:
        return request


class _NonCallableMiddleware:
    """A middleware component where a required attribute is not callable."""

    process_request = "not-a-callable"
    process_response = "also-not-callable"


# Map hook names to their valid component factory
_HOOK_TO_VALID_COMPONENT = {
    REGISTER_MIDDLEWARE: _ValidMiddleware,
    REGISTER_AUTH_PROVIDER: _ValidAuthProvider,
    REGISTER_SERIALIZER: _ValidSerializer,
    REGISTER_TEMPLATE_ENGINE: _ValidTemplateEngine,
    REGISTER_ERROR_HANDLER: _ValidErrorHandler,
    REGISTER_CLI_COMMAND: _ValidCliCommand,
}

# Map hook names to their fire method name
_HOOK_TO_FIRE_METHOD = {
    REGISTER_MIDDLEWARE: "fire_register_middleware",
    REGISTER_AUTH_PROVIDER: "fire_register_auth_provider",
    REGISTER_SERIALIZER: "fire_register_serializer",
    REGISTER_TEMPLATE_ENGINE: "fire_register_template_engine",
    REGISTER_ERROR_HANDLER: "fire_register_error_handler",
    REGISTER_CLI_COMMAND: "fire_register_cli_command",
}


# =============================================================================
# Unit Tests for Hook Name Constants
# =============================================================================

def test_hook_name_constants_are_strings():
    """
        Test that all component registration hook name constants are strings.
    """
    constants = [
        REGISTER_MIDDLEWARE,
        REGISTER_AUTH_PROVIDER,
        REGISTER_SERIALIZER,
        REGISTER_TEMPLATE_ENGINE,
        REGISTER_ERROR_HANDLER,
        REGISTER_CLI_COMMAND,
    ]

    for constant in constants:
        if not isinstance(constant, str):
            errmsg = "Hook constant should be a string, got {}".format(type(constant))
            raise AssertionError(errmsg)

    return


def test_hook_name_constants_have_expected_values():
    """
        Test that hook name constants have the expected string values.
    """
    expected = {
        REGISTER_MIDDLEWARE: "register_middleware",
        REGISTER_AUTH_PROVIDER: "register_auth_provider",
        REGISTER_SERIALIZER: "register_serializer",
        REGISTER_TEMPLATE_ENGINE: "register_template_engine",
        REGISTER_ERROR_HANDLER: "register_error_handler",
        REGISTER_CLI_COMMAND: "register_cli_command",
    }

    for constant, expected_value in expected.items():
        if constant != expected_value:
            errmsg = "Expected '{}', got '{}'".format(expected_value, constant)
            raise AssertionError(errmsg)

    return


def test_component_registration_hooks_list_contains_all_hooks():
    """
        Test that COMPONENT_REGISTRATION_HOOKS contains all six hook names.
    """
    expected_hooks = [
        REGISTER_MIDDLEWARE,
        REGISTER_AUTH_PROVIDER,
        REGISTER_SERIALIZER,
        REGISTER_TEMPLATE_ENGINE,
        REGISTER_ERROR_HANDLER,
        REGISTER_CLI_COMMAND,
    ]

    if len(COMPONENT_REGISTRATION_HOOKS) != len(expected_hooks):
        errmsg = "Expected {} hooks in list, got {}".format(
            len(expected_hooks), len(COMPONENT_REGISTRATION_HOOKS)
        )
        raise AssertionError(errmsg)

    for hook_name in expected_hooks:
        if hook_name not in COMPONENT_REGISTRATION_HOOKS:
            errmsg = "Hook '{}' not found in COMPONENT_REGISTRATION_HOOKS".format(hook_name)
            raise AssertionError(errmsg)

    return


# =============================================================================
# Unit Tests for ComponentRegistrationHooks
# =============================================================================

def test_component_registration_hooks_initial_state():
    """
        Test that a newly created ComponentRegistrationHooks has correct initial state.
    """
    manager = HookManager()
    hooks = ComponentRegistrationHooks(hook_manager=manager)

    if hooks.hook_manager is not manager:
        errmsg = "hook_manager property should return the provided HookManager"
        raise AssertionError(errmsg)

    if not isinstance(hooks.validator, ComponentValidator):
        errmsg = "validator property should return a ComponentValidator instance"
        raise AssertionError(errmsg)

    return


def test_fire_register_middleware_with_valid_component():
    """
        Test that fire_register_middleware accepts a valid middleware component.
    """
    manager = HookManager()
    hooks = ComponentRegistrationHooks(hook_manager=manager)

    component = _ValidMiddleware()
    hooks.fire_register_middleware(component)

    registered = hooks.get_registered_components(REGISTER_MIDDLEWARE)
    if len(registered) != 1:
        errmsg = "Expected 1 registered middleware, got {}".format(len(registered))
        raise AssertionError(errmsg)

    if registered[0] is not component:
        errmsg = "Registered component should be the same instance"
        raise AssertionError(errmsg)

    return


def test_fire_register_auth_provider_with_valid_component():
    """
        Test that fire_register_auth_provider accepts a valid auth provider.
    """
    manager = HookManager()
    hooks = ComponentRegistrationHooks(hook_manager=manager)

    component = _ValidAuthProvider()
    hooks.fire_register_auth_provider(component)

    registered = hooks.get_registered_components(REGISTER_AUTH_PROVIDER)
    if len(registered) != 1:
        errmsg = "Expected 1 registered auth provider, got {}".format(len(registered))
        raise AssertionError(errmsg)

    return


def test_fire_register_serializer_with_valid_component():
    """
        Test that fire_register_serializer accepts a valid serializer.
    """
    manager = HookManager()
    hooks = ComponentRegistrationHooks(hook_manager=manager)

    component = _ValidSerializer()
    hooks.fire_register_serializer(component)

    registered = hooks.get_registered_components(REGISTER_SERIALIZER)
    if len(registered) != 1:
        errmsg = "Expected 1 registered serializer, got {}".format(len(registered))
        raise AssertionError(errmsg)

    return


def test_fire_register_template_engine_with_valid_component():
    """
        Test that fire_register_template_engine accepts a valid template engine.
    """
    manager = HookManager()
    hooks = ComponentRegistrationHooks(hook_manager=manager)

    component = _ValidTemplateEngine()
    hooks.fire_register_template_engine(component)

    registered = hooks.get_registered_components(REGISTER_TEMPLATE_ENGINE)
    if len(registered) != 1:
        errmsg = "Expected 1 registered template engine, got {}".format(len(registered))
        raise AssertionError(errmsg)

    return


def test_fire_register_error_handler_with_valid_component():
    """
        Test that fire_register_error_handler accepts a valid error handler.
    """
    manager = HookManager()
    hooks = ComponentRegistrationHooks(hook_manager=manager)

    component = _ValidErrorHandler()
    hooks.fire_register_error_handler(component)

    registered = hooks.get_registered_components(REGISTER_ERROR_HANDLER)
    if len(registered) != 1:
        errmsg = "Expected 1 registered error handler, got {}".format(len(registered))
        raise AssertionError(errmsg)

    return


def test_fire_register_cli_command_with_valid_component():
    """
        Test that fire_register_cli_command accepts a valid CLI command.
    """
    manager = HookManager()
    hooks = ComponentRegistrationHooks(hook_manager=manager)

    component = _ValidCliCommand()
    hooks.fire_register_cli_command(component)

    registered = hooks.get_registered_components(REGISTER_CLI_COMMAND)
    if len(registered) != 1:
        errmsg = "Expected 1 registered CLI command, got {}".format(len(registered))
        raise AssertionError(errmsg)

    return


def test_get_registered_components_returns_empty_for_unknown_hook():
    """
        Test that get_registered_components returns an empty list for a
        hook with no registered components.
    """
    manager = HookManager()
    hooks = ComponentRegistrationHooks(hook_manager=manager)

    registered = hooks.get_registered_components(REGISTER_MIDDLEWARE)
    if len(registered) != 0:
        errmsg = "Expected empty list, got {} items".format(len(registered))
        raise AssertionError(errmsg)

    return


def test_fire_hooks_trigger_hook_manager_callbacks():
    """
        Test that firing a component registration hook triggers callbacks
        registered on the HookManager.
    """
    manager = HookManager()
    hooks = ComponentRegistrationHooks(hook_manager=manager)

    received_components = []

    def on_middleware_registered(component):
        received_components.append(component)
        return None

    manager.register(
        REGISTER_MIDDLEWARE, on_middleware_registered,
        extension_name="ext-listener"
    )

    component = _ValidMiddleware()
    hooks.fire_register_middleware(component)

    if len(received_components) != 1:
        errmsg = "Expected hook callback to receive 1 component, got {}".format(
            len(received_components)
        )
        raise AssertionError(errmsg)

    if received_components[0] is not component:
        errmsg = "Hook callback should receive the same component instance"
        raise AssertionError(errmsg)

    return


def test_validation_can_be_skipped():
    """
        Test that validation can be skipped by passing validate=False.
    """
    manager = HookManager()
    hooks = ComponentRegistrationHooks(hook_manager=manager)

    invalid_component = _InvalidComponent()

    # This should not raise because validation is skipped
    hooks.fire_register_middleware(invalid_component, validate=False)

    registered = hooks.get_registered_components(REGISTER_MIDDLEWARE)
    if len(registered) != 1:
        errmsg = "Expected 1 registered component (validation skipped), got {}".format(
            len(registered)
        )
        raise AssertionError(errmsg)

    return


# =============================================================================
# Unit Tests for ComponentValidator
# =============================================================================

def test_validator_accepts_valid_middleware():
    """
        Test that the validator accepts a component with all required methods.
    """
    validator = ComponentValidator()
    component = _ValidMiddleware()

    # Should not raise
    validator.validate(REGISTER_MIDDLEWARE, component)

    return


def test_validator_rejects_missing_method():
    """
        Test that the validator rejects a component missing a required method.
    """
    validator = ComponentValidator()
    component = _PartialMiddleware()

    raised = False
    try:
        validator.validate(REGISTER_MIDDLEWARE, component)
    except ExtensionPointError:
        raised = True

    if raised is not True:
        errmsg = "Expected ExtensionPointError for component missing process_response"
        raise AssertionError(errmsg)

    return


def test_validator_rejects_non_callable_attribute():
    """
        Test that the validator rejects a component where a required
        attribute is not callable.
    """
    validator = ComponentValidator()
    component = _NonCallableMiddleware()

    raised = False
    try:
        validator.validate(REGISTER_MIDDLEWARE, component)
    except ExtensionPointError:
        raised = True

    if raised is not True:
        errmsg = "Expected ExtensionPointError for non-callable attribute"
        raise AssertionError(errmsg)

    return


def test_validator_accepts_unknown_hook_name():
    """
        Test that the validator does not raise for an unknown hook name
        (no required methods defined).
    """
    validator = ComponentValidator()
    component = _InvalidComponent()

    # Should not raise because there are no required methods for unknown hooks
    validator.validate("unknown_hook", component)

    return


def test_validator_rejects_completely_invalid_component():
    """
        Test that the validator rejects a component with no required methods
        for each known hook type.
    """
    validator = ComponentValidator()
    component = _InvalidComponent()

    for hook_name in COMPONENT_REGISTRATION_HOOKS:
        raised = False
        try:
            validator.validate(hook_name, component)
        except ExtensionPointError:
            raised = True

        if raised is not True:
            errmsg = (
                "Expected ExtensionPointError for invalid component "
                "registered via '{}'"
            ).format(hook_name)
            raise AssertionError(errmsg)

    return


def test_fire_register_middleware_rejects_invalid_component():
    """
        Test that fire_register_middleware raises ExtensionPointError
        for an invalid component when validation is enabled.
    """
    manager = HookManager()
    hooks = ComponentRegistrationHooks(hook_manager=manager)

    component = _InvalidComponent()

    raised = False
    try:
        hooks.fire_register_middleware(component)
    except ExtensionPointError:
        raised = True

    if raised is not True:
        errmsg = "Expected ExtensionPointError for invalid middleware component"
        raise AssertionError(errmsg)

    # Verify the component was not registered
    registered = hooks.get_registered_components(REGISTER_MIDDLEWARE)
    if len(registered) != 0:
        errmsg = "Invalid component should not be registered, got {} items".format(
            len(registered)
        )
        raise AssertionError(errmsg)

    return


# =============================================================================
# Property Tests
# =============================================================================

def test_property_20_component_registration_hooks():
    """
        Property 20: Component Registration Hooks

        For any component registered via register_middleware,
        register_auth_provider, register_serializer, register_template_engine,
        register_error_handler, or register_cli_command hooks, the component
        SHALL be available through the standard framework APIs.

        This property verifies that for each hook type, registering a valid
        component makes it retrievable via get_registered_components, and
        that hook callbacks on the HookManager are fired with the component.

        **Validates: Requirements 7.1, 7.2, 7.3, 7.4, 7.5, 7.6, 7.7**
    """
    for iteration in range(100):
        manager = HookManager()
        hooks = ComponentRegistrationHooks(hook_manager=manager)

        # Randomly select a subset of hook types to register components for
        num_hooks = random.randint(1, len(COMPONENT_REGISTRATION_HOOKS))
        selected_hooks = random.sample(COMPONENT_REGISTRATION_HOOKS, k=num_hooks)

        # Track components received by hook callbacks
        callback_received: dict = {}

        for hook_name in selected_hooks:
            callback_received[hook_name] = []

            def make_cb(hname):
                def cb(component):
                    callback_received[hname].append(component)
                    return None
                return cb

            manager.register(hook_name, make_cb(hook_name), extension_name="ext-listener")

        # Register a random number of valid components for each selected hook
        expected_components: dict = {}

        for hook_name in selected_hooks:
            num_components = random.randint(1, 3)
            expected_components[hook_name] = []

            component_cls = _HOOK_TO_VALID_COMPONENT[hook_name]
            fire_method_name = _HOOK_TO_FIRE_METHOD[hook_name]
            fire_method = getattr(hooks, fire_method_name)

            for _ in range(num_components):
                component = component_cls()
                expected_components[hook_name].append(component)
                fire_method(component)

        # Verify all components are retrievable
        for hook_name in selected_hooks:
            registered = hooks.get_registered_components(hook_name)
            expected = expected_components[hook_name]

            if len(registered) != len(expected):
                errmsg = (
                    "Iteration {}: Hook '{}' expected {} registered components, "
                    "got {}"
                ).format(iteration, hook_name, len(expected), len(registered))
                raise AssertionError(errmsg)

            for idx in range(len(expected)):
                if registered[idx] is not expected[idx]:
                    errmsg = (
                        "Iteration {}: Hook '{}' component at index {} is not "
                        "the same instance"
                    ).format(iteration, hook_name, idx)
                    raise AssertionError(errmsg)

        # Verify hook callbacks received the components
        for hook_name in selected_hooks:
            received = callback_received[hook_name]
            expected = expected_components[hook_name]

            if len(received) != len(expected):
                errmsg = (
                    "Iteration {}: Hook '{}' callback expected {} components, "
                    "received {}"
                ).format(iteration, hook_name, len(expected), len(received))
                raise AssertionError(errmsg)

            for idx in range(len(expected)):
                if received[idx] is not expected[idx]:
                    errmsg = (
                        "Iteration {}: Hook '{}' callback component at index {} "
                        "is not the same instance"
                    ).format(iteration, hook_name, idx)
                    raise AssertionError(errmsg)

        # Verify hooks not selected have no registered components
        for hook_name in COMPONENT_REGISTRATION_HOOKS:
            if hook_name not in selected_hooks:
                registered = hooks.get_registered_components(hook_name)
                if len(registered) != 0:
                    errmsg = (
                        "Iteration {}: Hook '{}' should have no registered "
                        "components, got {}"
                    ).format(iteration, hook_name, len(registered))
                    raise AssertionError(errmsg)

    return


def test_property_21_component_interface_validation():
    """
        Property 21: Component Interface Validation

        For any component registered via a registration hook, the framework
        SHALL validate that it implements the required interface and reject
        invalid components.

        This property verifies that for each hook type, components missing
        required methods are rejected with ExtensionPointError, and valid
        components are accepted.

        **Validates: Requirements 7.8**
    """
    for iteration in range(100):
        manager = HookManager()
        hooks = ComponentRegistrationHooks(hook_manager=manager)

        # Randomly select a hook type
        hook_name = random.choice(COMPONENT_REGISTRATION_HOOKS)
        fire_method_name = _HOOK_TO_FIRE_METHOD[hook_name]
        fire_method = getattr(hooks, fire_method_name)
        required_methods = COMPONENT_REQUIRED_METHODS[hook_name]

        # Test 1: Valid component should be accepted
        valid_cls = _HOOK_TO_VALID_COMPONENT[hook_name]
        valid_component = valid_cls()

        accepted = True
        try:
            fire_method(valid_component)
        except ExtensionPointError:
            accepted = False

        if accepted is not True:
            errmsg = (
                "Iteration {}: Valid component for '{}' should be accepted"
            ).format(iteration, hook_name)
            raise AssertionError(errmsg)

        # Test 2: Component with no methods should be rejected
        invalid_component = _InvalidComponent()

        rejected = False
        try:
            fire_method(invalid_component)
        except ExtensionPointError:
            rejected = True

        if rejected is not True:
            errmsg = (
                "Iteration {}: Invalid component for '{}' should be rejected"
            ).format(iteration, hook_name)
            raise AssertionError(errmsg)

        # Test 3: Dynamically create a component missing one random method
        if len(required_methods) > 1:
            missing_method = random.choice(required_methods)

            class _DynamicPartial:
                pass

            partial = _DynamicPartial()
            for method_name in required_methods:
                if method_name != missing_method:
                    setattr(partial, method_name, lambda *args: None)

            partial_rejected = False
            try:
                fire_method(partial)
            except ExtensionPointError:
                partial_rejected = True

            if partial_rejected is not True:
                errmsg = (
                    "Iteration {}: Component for '{}' missing method '{}' "
                    "should be rejected"
                ).format(iteration, hook_name, missing_method)
                raise AssertionError(errmsg)

        # Verify only the valid component was registered
        registered = hooks.get_registered_components(hook_name)
        if len(registered) != 1:
            errmsg = (
                "Iteration {}: Expected exactly 1 registered component for '{}' "
                "(only the valid one), got {}"
            ).format(iteration, hook_name, len(registered))
            raise AssertionError(errmsg)

        if registered[0] is not valid_component:
            errmsg = (
                "Iteration {}: Registered component for '{}' should be the "
                "valid component instance"
            ).format(iteration, hook_name)
            raise AssertionError(errmsg)

    return
