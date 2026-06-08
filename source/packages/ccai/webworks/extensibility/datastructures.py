"""
    Core data structures and enums for the extensibility system.

    This module defines the fundamental data types used throughout the
    extensibility framework including extension states, hook priorities,
    and registration data structures.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Type


class ExtensionState(Enum):
    """
        States an extension can be in during its lifecycle.

        Extensions transition through these states as they are
        registered, initialized, activated, disabled, or encounter errors.
    """

    UNKNOWN = "unknown"
    REGISTERED = "registered"
    INITIALIZED = "initialized"
    ACTIVE = "active"
    DISABLED = "disabled"
    ERROR = "error"
    QUARANTINED = "quarantined"


class HookPriority:
    """
        Named priority constants for hook ordering.

        Lower numeric values execute first. These constants provide
        well-known priority levels for common use cases.
    """

    HIGHEST = 0
    HIGH = 25
    NORMAL = 50
    LOW = 75
    LOWEST = 100


@dataclass
class HookRegistration:
    """
        A registered hook callback with priority and ordering constraints.

        :param callback: The callable to invoke when the hook fires.
        :param priority: Numeric priority value (lower executes first).
        :param extension_name: The name of the extension that registered this hook.
        :param before: List of extension names this hook should run before.
        :param after: List of extension names this hook should run after.
    """

    callback: Callable
    priority: int
    extension_name: Optional[str]
    before: List[str] = field(default_factory=list)
    after: List[str] = field(default_factory=list)


@dataclass
class ExtensionPointDefinition:
    """
        Definition of an extension point that other extensions can contribute to.

        :param name: The unique name of the extension point.
        :param interface: The type that contributions must implement.
        :param description: A human-readable description of the extension point.
        :param multiple: Whether multiple contributions are allowed.
    """

    name: str
    interface: Type
    description: str = ""
    multiple: bool = True


@dataclass
class LifecycleEvent:
    """
        An extension lifecycle event for observability.

        :param event_type: The type of lifecycle event that occurred.
        :param extension_name: The name of the extension involved.
        :param timestamp: When the event occurred.
        :param data: Additional event-specific data.
    """

    event_type: str
    extension_name: str
    timestamp: datetime
    data: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ExtensionErrorInfo:
    """
        Information about an error that occurred in an extension.

        :param extension_name: The name of the extension that errored.
        :param hook_name: The hook being executed when the error occurred, if applicable.
        :param exception: The exception that was raised.
        :param timestamp: When the error occurred.
        :param stack_trace: The formatted stack trace string.
    """

    extension_name: str
    hook_name: Optional[str]
    exception: Exception
    timestamp: datetime
    stack_trace: str
