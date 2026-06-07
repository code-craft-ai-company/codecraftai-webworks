"""
    Decorators for the extensibility system.

    This module provides decorators for declaring extension points
    and other extensibility metadata on classes and functions.
"""

from typing import Optional, Type

from ccai.webworks.extensibility.datastructures import ExtensionPointDefinition


# Module-level registry of extension point definitions declared via decorator.
# This is populated at import time when @extension_point is used, and later
# consumed by the ExtensionRegistry during initialization.
_extension_point_definitions: dict = {}


def extension_point(name: str, interface: Type, description: str = "", multiple: bool = True):
    """
        Decorator that declares an extension point.

        Registers an ExtensionPointDefinition with the given name and
        interface specification. The decorated class or function is
        returned unchanged.

        :param name: The unique name of the extension point.
        :param interface: The type that contributions must implement.
        :param description: A human-readable description of the extension point.
        :param multiple: Whether multiple contributions are allowed.

        :returns: A decorator that registers the extension point and returns
                  the decorated target unchanged.
    """

    def decorator(target):
        definition = ExtensionPointDefinition(
            name=name,
            interface=interface,
            description=description,
            multiple=multiple
        )

        _extension_point_definitions[name] = definition

        return target

    return decorator


def get_registered_extension_points() -> dict:
    """
        Get all extension point definitions registered via the decorator.

        :returns: A dictionary mapping extension point names to their definitions.
    """
    rtnval = dict(_extension_point_definitions)
    return rtnval


def clear_registered_extension_points() -> None:
    """
        Clear all registered extension point definitions.

        This is primarily useful for testing to reset state between tests.
    """
    _extension_point_definitions.clear()
    return
