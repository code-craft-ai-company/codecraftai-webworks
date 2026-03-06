"""
.. module:: lifecycle
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: Module containing the :class:`LifecyclePhase` enum for tracking
        web application startup phases, and error classes for lifecycle
        enforcement: :class:`LifecycleError`, :class:`BlueprintAlreadyRegisteredError`,
        and :class:`EndpointConflictError`.

.. moduleauthor:: Automation Mojo LLC
"""

__author__ = "Automation Mojo LLC"
__copyright__ = "Copyright 2025, Automation Mojo LLC"
__credits__ = []


from enum import Enum
from typing import Optional, Type

from automojo.errors.exceptions import SemanticError


# ---------------------------------------------------------------------------
# Lifecycle Phase Enum
# ---------------------------------------------------------------------------
class LifecyclePhase(str, Enum):
    """
        Enum representing the discrete phases of the WebApplication startup
        lifecycle.  Members are declared in dependency order so that ordinal
        comparison (via ``list(LifecyclePhase).index()``) can enforce that
        prerequisite phases have completed before dependent operations execute.
    """

    CREATED = "created"
    CONFIGURED = "configured"
    CREDENTIALS_LOADED = "credentials_loaded"
    DATA_PROFILES_LOADED = "data_profiles_loaded"
    DATABASE_READY = "database_ready"
    AUTHENTICATION_READY = "authentication_ready"
    INFRASTRUCTURE_READY = "infrastructure_ready"
    READY = "ready"
    SHUTDOWN = "shutdown"


# ---------------------------------------------------------------------------
# Lifecycle Errors
# ---------------------------------------------------------------------------
class LifecycleError(SemanticError):
    """
        Raised when a caller attempts an operation that depends on a lifecycle
        phase that has not yet completed.

        :param operation: The name of the operation that was attempted.
        :param required_phase: The minimum lifecycle phase required for the
            operation.
        :param current_phase: The lifecycle phase the application is currently
            in.
    """

    def __init__(self, operation: str, required_phase: LifecyclePhase,
                 current_phase: LifecyclePhase):
        self.operation = operation
        self.required_phase = required_phase
        self.current_phase = current_phase

        errmsg = (
            f"Cannot perform '{operation}': requires phase '{required_phase.value}' "
            f"but current phase is '{current_phase.value}'."
        )
        super().__init__(errmsg)
        return


class BlueprintAlreadyRegisteredError(SemanticError):
    """
        Raised when ``attach_blueprint_to_route`` is called with a
        :class:`RestBlueprint` class that has already been registered
        with the WebApplication.

        :param blueprint_cls: The blueprint class that was already registered.
    """

    def __init__(self, blueprint_cls: Type):
        self.blueprint_cls = blueprint_cls

        errmsg = (
            f"Blueprint '{blueprint_cls.__name__}' has already been registered. "
            f"Duplicate registration is not allowed."
        )
        super().__init__(errmsg)
        return


class EndpointConflictError(SemanticError):
    """
        Raised when ``attach_route`` detects a routing conflict — for example,
        when a handler is registered at a path and HTTP method combination that
        is already occupied.  This error wraps the lower-level
        :class:`~automojo.webworks.routing.exceptions.RoutingError` to provide
        a lifecycle-scoped error type.

        :param path: The URL path that caused the conflict.
        :param method: The HTTP method that caused the conflict.
        :param detail: An optional detail message from the underlying routing
            layer.
    """

    def __init__(self, path: str, method: str,
                 detail: Optional[str] = None):
        self.path = path
        self.method = method
        self.detail = detail

        if detail is not None:
            errmsg = (
                f"Endpoint conflict at '{method} {path}': {detail}"
            )
        else:
            errmsg = (
                f"Endpoint conflict at '{method} {path}': a handler is already "
                f"registered for this path and method combination."
            )
        super().__init__(errmsg)
        return
