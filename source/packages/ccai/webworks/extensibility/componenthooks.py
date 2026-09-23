"""
    Component registration hooks for the extensibility system.

    This module defines the hook name constants, the ComponentRegistrationHooks
    class that wraps the HookManager to provide component registration hook
    execution, and the ComponentValidator class for validating that registered
    components implement required interfaces using duck-typing.

    The hooks allow extensions to register custom components such as middleware,
    authentication providers, serializers, template engines, error handlers,
    and CLI commands with the web framework.
"""

import logging

from typing import Any, Dict, List, Optional

from ccai.webworks.extensibility.exceptions import ExtensionPointError
from ccai.webworks.extensibility.hookmanager import HookManager


logger = logging.getLogger("ccai.webworks.extensibility.componenthooks")


# =============================================================================
# Component Registration Hook Name Constants
# =============================================================================

REGISTER_MIDDLEWARE = "register_middleware"
"""Hook called to register custom middleware."""

REGISTER_AUTH_PROVIDER = "register_auth_provider"
"""Hook called to register an authentication provider."""

REGISTER_SERIALIZER = "register_serializer"
"""Hook called to register a custom serializer."""

REGISTER_TEMPLATE_ENGINE = "register_template_engine"
"""Hook called to register a template engine."""

REGISTER_ERROR_HANDLER = "register_error_handler"
"""Hook called to register a custom error handler."""

REGISTER_CLI_COMMAND = "register_cli_command"
"""Hook called to register a CLI command."""


COMPONENT_REGISTRATION_HOOKS = [
    REGISTER_MIDDLEWARE,
    REGISTER_AUTH_PROVIDER,
    REGISTER_SERIALIZER,
    REGISTER_TEMPLATE_ENGINE,
    REGISTER_ERROR_HANDLER,
    REGISTER_CLI_COMMAND,
]
"""List of all component registration hook names."""


# =============================================================================
# Component Interface Definitions
# =============================================================================

# Maps each hook name to the list of method names that a component must
# implement in order to be considered valid for that hook type.
COMPONENT_REQUIRED_METHODS: Dict[str, List[str]] = {
    REGISTER_MIDDLEWARE: ["process_request", "process_response"],
    REGISTER_AUTH_PROVIDER: ["authenticate"],
    REGISTER_SERIALIZER: ["serialize", "deserialize"],
    REGISTER_TEMPLATE_ENGINE: ["render"],
    REGISTER_ERROR_HANDLER: ["handle_error"],
    REGISTER_CLI_COMMAND: ["execute"],
}
"""
    Mapping of hook names to the required method names that a component
    must implement for that hook type. Used by ComponentValidator for
    duck-typing validation.
"""


# =============================================================================
# ComponentValidator
# =============================================================================

class ComponentValidator:
    """
        Validates that a component implements the required interface for
        a given hook type using duck-typing.

        Duck-typing validation checks that the component has callable
        attributes matching the required method names for the hook type.
    """

    def __init__(self, required_methods: Optional[Dict[str, List[str]]] = None):
        """
            Initialize the ComponentValidator.

            :param required_methods: An optional mapping of hook names to lists
                of required method names. If None, the module-level
                COMPONENT_REQUIRED_METHODS mapping is used.
        """
        if required_methods is not None:
            self._required_methods = required_methods
        else:
            self._required_methods = COMPONENT_REQUIRED_METHODS
        return

    def validate(self, hook_name: str, component: Any) -> None:
        """
            Validate that a component implements the required interface
            for the given hook type.

            Uses duck-typing to check that the component has callable
            attributes matching each required method name.

            :param hook_name: The hook name identifying the component type.
            :param component: The component instance to validate.

            :raises: ExtensionPointError if the component does not implement
                     the required interface.
        """
        if hook_name not in self._required_methods:
            return

        required = self._required_methods[hook_name]

        for method_name in required:
            if not hasattr(component, method_name):
                errmsg = (
                    "Component registered via '{}' is missing required "
                    "method '{}'"
                ).format(hook_name, method_name)
                raise ExtensionPointError(message=errmsg, point_name=hook_name)

            attr = getattr(component, method_name)
            if not callable(attr):
                errmsg = (
                    "Component registered via '{}' has attribute '{}' "
                    "but it is not callable"
                ).format(hook_name, method_name)
                raise ExtensionPointError(message=errmsg, point_name=hook_name)

        return


# =============================================================================
# ComponentRegistrationHooks
# =============================================================================

class ComponentRegistrationHooks:
    """
        Wraps a HookManager to provide component registration hook execution.

        This class manages the firing of component registration hooks and
        optionally validates that registered components implement the required
        interfaces before passing them to hook callbacks. Each fire method
        delegates to the HookManager.execute() method which handles error
        isolation by catching exceptions from individual callbacks and
        continuing with the remaining callbacks.

        :param hook_manager: The HookManager instance to use for hook execution.
        :param validator: An optional ComponentValidator instance for interface
            validation. If None, a default ComponentValidator is created.
    """

    def __init__(self, hook_manager: HookManager, validator: Optional[ComponentValidator] = None):
        self._hook_manager = hook_manager
        if validator is not None:
            self._validator = validator
        else:
            self._validator = ComponentValidator()
        self._registered_components: Dict[str, List[Any]] = {}
        return

    @property
    def hook_manager(self) -> HookManager:
        """
            Get the underlying HookManager instance.

            :returns: The HookManager used by this instance.
        """
        return self._hook_manager

    @property
    def validator(self) -> ComponentValidator:
        """
            Get the ComponentValidator instance.

            :returns: The ComponentValidator used by this instance.
        """
        return self._validator

    def get_registered_components(self, hook_name: str) -> List[Any]:
        """
            Get all components registered for a given hook type.

            :param hook_name: The hook name identifying the component type.

            :returns: A list of registered component instances. Returns an
                empty list if no components are registered for the hook.
        """
        if hook_name not in self._registered_components:
            rtnval = []
        else:
            rtnval = list(self._registered_components[hook_name])
        return rtnval

    def _register_component(self, hook_name: str, component: Any, validate: bool = True) -> None:
        """
            Internal method to validate and store a component, then fire
            the corresponding hook.

            :param hook_name: The hook name identifying the component type.
            :param component: The component instance to register.
            :param validate: Whether to validate the component interface
                before registration. Defaults to True.

            :raises: ExtensionPointError if validation is enabled and the
                     component does not implement the required interface.
        """
        if validate is True:
            self._validator.validate(hook_name, component)

        if hook_name not in self._registered_components:
            self._registered_components[hook_name] = []

        self._registered_components[hook_name].append(component)

        self._hook_manager.execute(hook_name, component)

        return

    def fire_register_middleware(self, component: Any, validate: bool = True) -> None:
        """
            Register a middleware component.

            Optionally validates that the component implements the required
            middleware interface (process_request, process_response) before
            registration.

            :param component: The middleware component to register.
            :param validate: Whether to validate the component interface.

            :raises: ExtensionPointError if validation fails.
        """
        self._register_component(REGISTER_MIDDLEWARE, component, validate=validate)
        return

    def fire_register_auth_provider(self, component: Any, validate: bool = True) -> None:
        """
            Register an authentication provider component.

            Optionally validates that the component implements the required
            auth provider interface (authenticate) before registration.

            :param component: The auth provider component to register.
            :param validate: Whether to validate the component interface.

            :raises: ExtensionPointError if validation fails.
        """
        self._register_component(REGISTER_AUTH_PROVIDER, component, validate=validate)
        return

    def fire_register_serializer(self, component: Any, validate: bool = True) -> None:
        """
            Register a serializer component.

            Optionally validates that the component implements the required
            serializer interface (serialize, deserialize) before registration.

            :param component: The serializer component to register.
            :param validate: Whether to validate the component interface.

            :raises: ExtensionPointError if validation fails.
        """
        self._register_component(REGISTER_SERIALIZER, component, validate=validate)
        return

    def fire_register_template_engine(self, component: Any, validate: bool = True) -> None:
        """
            Register a template engine component.

            Optionally validates that the component implements the required
            template engine interface (render) before registration.

            :param component: The template engine component to register.
            :param validate: Whether to validate the component interface.

            :raises: ExtensionPointError if validation fails.
        """
        self._register_component(REGISTER_TEMPLATE_ENGINE, component, validate=validate)
        return

    def fire_register_error_handler(self, component: Any, validate: bool = True) -> None:
        """
            Register an error handler component.

            Optionally validates that the component implements the required
            error handler interface (handle_error) before registration.

            :param component: The error handler component to register.
            :param validate: Whether to validate the component interface.

            :raises: ExtensionPointError if validation fails.
        """
        self._register_component(REGISTER_ERROR_HANDLER, component, validate=validate)
        return

    def fire_register_cli_command(self, component: Any, validate: bool = True) -> None:
        """
            Register a CLI command component.

            Optionally validates that the component implements the required
            CLI command interface (execute) before registration.

            :param component: The CLI command component to register.
            :param validate: Whether to validate the component interface.

            :raises: ExtensionPointError if validation fails.
        """
        self._register_component(REGISTER_CLI_COMMAND, component, validate=validate)
        return
