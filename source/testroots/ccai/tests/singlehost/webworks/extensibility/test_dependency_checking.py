"""
    Property-based test for dependency availability checking.

    This module contains the property-based test for Property 34:
    Dependency Availability Check. It validates that has_dependency()
    returns True when a dependency is registered and available, and
    get_dependency() returns the dependency extension instance.
"""

import random
import string

from typing import Any, Dict, List, Optional

from ccai.webworks.extensibility.context import ExtensionContext


# =============================================================================
# Test Helpers
# =============================================================================

class _FakeExtension:
    """
        A fake extension for testing dependency lookups.
    """

    def __init__(self, name: str):
        self.name = name
        return


class _FakeExtensionRegistry:
    """
        A fake extension registry for testing dependency lookups.

        Stores extensions by name and supports the get() method
        used by ExtensionContext.has_dependency() and get_dependency().
    """

    def __init__(self, extensions: Optional[Dict[str, Any]] = None):
        self._extensions = extensions if extensions is not None else {}
        return

    def get(self, name: str) -> Optional[Any]:
        """
            Get an extension by name.

            :param name: The extension name.

            :returns: The extension or None if not found.
        """
        rtnval = self._extensions.get(name, None)
        return rtnval


class _FakeAppContext:
    """
        A fake application context for testing purposes.

        Provides the duck-typed interface that ExtensionContext
        expects from the application context, including the
        extension_registry attribute used by dependency methods.
    """

    def __init__(self, extension_registry: Optional[Any] = None):
        self.config = {}
        self.endpoint_registry = None
        self.url_node_map = None
        self.middleware = []
        self.extension_registry = extension_registry if extension_registry is not None else _FakeExtensionRegistry()
        return

    def get_logger(self, name: str):
        """
            Get a logger by name.

            :param name: The logger name.

            :returns: None (not needed for dependency tests).
        """
        return None


# =============================================================================
# Random Data Generators
# =============================================================================

def _generate_random_name(min_length: int = 3, max_length: int = 20) -> str:
    """
        Generate a random extension name using lowercase letters and hyphens.

        :param min_length: Minimum length of the generated name.
        :param max_length: Maximum length of the generated name.

        :returns: A random extension name string.
    """
    length = random.randint(min_length, max_length)
    chars = string.ascii_lowercase + string.digits + "-"
    # Ensure the name starts with a letter
    first_char = random.choice(string.ascii_lowercase)
    rest = "".join(random.choices(chars, k=length - 1))
    result = first_char + rest
    return result


def _generate_unique_names(count: int) -> List[str]:
    """
        Generate a list of unique random extension names.

        :param count: The number of unique names to generate.

        :returns: A list of unique random extension name strings.
    """
    names = set()
    while len(names) < count:
        name = _generate_random_name(5, 20)
        names.add(name)

    result = list(names)
    return result


# =============================================================================
# Property-Based Tests
# =============================================================================

# Feature: extensibility, Property 34: Dependency Availability Check
# *For any* extension, calling has_dependency() SHALL return True if the
# dependency is registered and available, and get_dependency() SHALL
# return the dependency extension.
# **Validates: Requirements 12.7, 12.8**

def test_property_34_dependency_availability_check():
    """
        Property 34: Dependency Availability Check

        For any random set of registered extensions, has_dependency()
        SHALL return True when the dependency is registered and
        available, and False when it is not. get_dependency() SHALL
        return the extension instance when available, and None when
        it is not.

        **Validates: Requirements 12.7, 12.8**
    """
    for iteration in range(100):
        # Generate a random number of registered extensions
        registered_count = random.randint(1, 10)
        registered_names = _generate_unique_names(registered_count)

        # Create fake extension instances for each registered name
        registered_extensions = {}
        for name in registered_names:
            registered_extensions[name] = _FakeExtension(name=name)

        # Build the fake registry and app context
        ext_registry = _FakeExtensionRegistry(extensions=registered_extensions)
        app_ctx = _FakeAppContext(extension_registry=ext_registry)

        # Create the context under test
        context_name = _generate_random_name(3, 15)
        ctx = ExtensionContext(
            extension_name=context_name,
            app_context=app_ctx,
            config={}
        )

        # Verify has_dependency() returns True for all registered extensions
        for name in registered_names:
            result = ctx.has_dependency(name)
            if result is not True:
                errmsg = (
                    "Iteration {}: has_dependency('{}') returned {} "
                    "but expected True for a registered extension"
                ).format(iteration, name, result)
                raise AssertionError(errmsg)

        # Verify get_dependency() returns the correct extension instance
        for name in registered_names:
            result = ctx.get_dependency(name)
            expected = registered_extensions[name]
            if result is not expected:
                errmsg = (
                    "Iteration {}: get_dependency('{}') did not return "
                    "the expected extension instance"
                ).format(iteration, name)
                raise AssertionError(errmsg)

        # Generate names that are NOT registered and verify unavailability
        unregistered_count = random.randint(1, 5)
        unregistered_names = _generate_unique_names(unregistered_count + registered_count)
        # Filter out any names that happen to collide with registered ones
        unregistered_names = [n for n in unregistered_names if n not in registered_extensions]

        for name in unregistered_names:
            has_result = ctx.has_dependency(name)
            if has_result is not False:
                errmsg = (
                    "Iteration {}: has_dependency('{}') returned {} "
                    "but expected False for an unregistered extension"
                ).format(iteration, name, has_result)
                raise AssertionError(errmsg)

            get_result = ctx.get_dependency(name)
            if get_result is not None:
                errmsg = (
                    "Iteration {}: get_dependency('{}') returned {} "
                    "but expected None for an unregistered extension"
                ).format(iteration, name, get_result)
                raise AssertionError(errmsg)

        # Verify consistency: has_dependency and get_dependency agree
        all_names = registered_names + unregistered_names
        for name in all_names:
            has_it = ctx.has_dependency(name)
            got_it = ctx.get_dependency(name)

            if has_it is True and got_it is None:
                errmsg = (
                    "Iteration {}: has_dependency('{}') is True but "
                    "get_dependency returned None - inconsistent"
                ).format(iteration, name)
                raise AssertionError(errmsg)

            if has_it is False and got_it is not None:
                errmsg = (
                    "Iteration {}: has_dependency('{}') is False but "
                    "get_dependency returned a value - inconsistent"
                ).format(iteration, name)
                raise AssertionError(errmsg)

    return
