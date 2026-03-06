"""
.. module:: test_lifecycle
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: Unit tests for the :class:`LifecyclePhase` enum and lifecycle
        error classes: :class:`LifecycleError`, :class:`BlueprintAlreadyRegisteredError`,
        and :class:`EndpointConflictError`.

.. moduleauthor:: Automation Mojo LLC
"""

__author__ = "Automation Mojo LLC"
__copyright__ = "Copyright 2025, Automation Mojo LLC"
__credits__ = []


from automojo.webworks.persona.lifecycle import (
    LifecyclePhase,
    LifecycleError,
    BlueprintAlreadyRegisteredError,
    EndpointConflictError,
)
from automojo.errors.exceptions import SemanticError


# =============================================================================
# Unit Tests for LifecyclePhase Enum
# =============================================================================

def test_lifecycle_phase_has_all_expected_members():
    """
        Test that LifecyclePhase contains exactly the expected members.
    """
    expected_names = [
        "CREATED",
        "CONFIGURED",
        "CREDENTIALS_LOADED",
        "DATA_PROFILES_LOADED",
        "DATABASE_READY",
        "AUTHENTICATION_READY",
        "INFRASTRUCTURE_READY",
        "READY",
        "SHUTDOWN",
    ]

    actual_names = [member.name for member in LifecyclePhase]

    if actual_names != expected_names:
        errmsg = (
            f"LifecyclePhase members do not match expected.\n"
            f"  Expected: {expected_names}\n"
            f"  Actual:   {actual_names}"
        )
        raise AssertionError(errmsg)

    return


def test_lifecycle_phase_members_are_in_correct_order():
    """
        Test that LifecyclePhase members are declared in the correct
        dependency order so that ordinal comparison works for phase
        enforcement.
    """
    members = list(LifecyclePhase)

    created_index = members.index(LifecyclePhase.CREATED)
    configured_index = members.index(LifecyclePhase.CONFIGURED)
    credentials_index = members.index(LifecyclePhase.CREDENTIALS_LOADED)
    data_profiles_index = members.index(LifecyclePhase.DATA_PROFILES_LOADED)
    database_index = members.index(LifecyclePhase.DATABASE_READY)
    auth_index = members.index(LifecyclePhase.AUTHENTICATION_READY)
    infra_index = members.index(LifecyclePhase.INFRASTRUCTURE_READY)
    ready_index = members.index(LifecyclePhase.READY)
    shutdown_index = members.index(LifecyclePhase.SHUTDOWN)

    if not (created_index < configured_index < credentials_index
            < data_profiles_index < database_index < auth_index
            < infra_index < ready_index < shutdown_index):
        errmsg = (
            "LifecyclePhase members are not in the expected dependency order.\n"
            f"  Indices: CREATED={created_index}, CONFIGURED={configured_index}, "
            f"CREDENTIALS_LOADED={credentials_index}, DATA_PROFILES_LOADED={data_profiles_index}, "
            f"DATABASE_READY={database_index}, AUTHENTICATION_READY={auth_index}, "
            f"INFRASTRUCTURE_READY={infra_index}, READY={ready_index}, SHUTDOWN={shutdown_index}"
        )
        raise AssertionError(errmsg)

    return


def test_lifecycle_phase_is_string_enum():
    """
        Test that LifecyclePhase members are string values, allowing
        direct string comparison.
    """
    phase = LifecyclePhase.CREATED

    if not isinstance(phase, str):
        errmsg = f"Expected LifecyclePhase member to be a str instance, got {type(phase)}"
        raise AssertionError(errmsg)

    if phase.value != "created":
        errmsg = f"Expected CREATED value to be 'created', got '{phase.value}'"
        raise AssertionError(errmsg)

    return


def test_lifecycle_phase_member_count():
    """
        Test that LifecyclePhase has exactly 9 members.
    """
    member_count = len(LifecyclePhase)

    if member_count != 9:
        errmsg = f"Expected 9 LifecyclePhase members, got {member_count}"
        raise AssertionError(errmsg)

    return


# =============================================================================
# Unit Tests for LifecycleError
# =============================================================================

def test_lifecycle_error_extends_semantic_error():
    """
        Test that LifecycleError is a subclass of SemanticError.
    """
    if not issubclass(LifecycleError, SemanticError):
        errmsg = "Expected LifecycleError to be a subclass of SemanticError"
        raise AssertionError(errmsg)

    return


def test_lifecycle_error_message_includes_operation():
    """
        Test that the LifecycleError message includes the operation name.
    """
    operation = "configure_auth_middleware"
    required_phase = LifecyclePhase.INFRASTRUCTURE_READY
    current_phase = LifecyclePhase.CREATED

    error = LifecycleError(
        operation=operation,
        required_phase=required_phase,
        current_phase=current_phase,
    )
    error_message = str(error)

    if operation not in error_message:
        errmsg = (
            f"Expected error message to include operation '{operation}'.\n"
            f"  Actual message: {error_message}"
        )
        raise AssertionError(errmsg)

    return


def test_lifecycle_error_message_includes_required_phase():
    """
        Test that the LifecycleError message includes the required phase value.
    """
    operation = "access_router"
    required_phase = LifecyclePhase.INFRASTRUCTURE_READY
    current_phase = LifecyclePhase.CONFIGURED

    error = LifecycleError(
        operation=operation,
        required_phase=required_phase,
        current_phase=current_phase,
    )
    error_message = str(error)

    if required_phase.value not in error_message:
        errmsg = (
            f"Expected error message to include required phase '{required_phase.value}'.\n"
            f"  Actual message: {error_message}"
        )
        raise AssertionError(errmsg)

    return


def test_lifecycle_error_message_includes_current_phase():
    """
        Test that the LifecycleError message includes the current phase value.
    """
    operation = "access_router"
    required_phase = LifecyclePhase.INFRASTRUCTURE_READY
    current_phase = LifecyclePhase.CREATED

    error = LifecycleError(
        operation=operation,
        required_phase=required_phase,
        current_phase=current_phase,
    )
    error_message = str(error)

    if current_phase.value not in error_message:
        errmsg = (
            f"Expected error message to include current phase '{current_phase.value}'.\n"
            f"  Actual message: {error_message}"
        )
        raise AssertionError(errmsg)

    return


def test_lifecycle_error_stores_attributes():
    """
        Test that LifecycleError stores the operation, required_phase,
        and current_phase as accessible attributes.
    """
    operation = "setup_infrastructure"
    required_phase = LifecyclePhase.AUTHENTICATION_READY
    current_phase = LifecyclePhase.CONFIGURED

    error = LifecycleError(
        operation=operation,
        required_phase=required_phase,
        current_phase=current_phase,
    )

    if error.operation != operation:
        errmsg = f"Expected operation '{operation}', got '{error.operation}'"
        raise AssertionError(errmsg)

    if error.required_phase != required_phase:
        errmsg = f"Expected required_phase '{required_phase}', got '{error.required_phase}'"
        raise AssertionError(errmsg)

    if error.current_phase != current_phase:
        errmsg = f"Expected current_phase '{current_phase}', got '{error.current_phase}'"
        raise AssertionError(errmsg)

    return


# =============================================================================
# Unit Tests for BlueprintAlreadyRegisteredError
# =============================================================================

def test_blueprint_already_registered_error_extends_semantic_error():
    """
        Test that BlueprintAlreadyRegisteredError is a subclass of SemanticError.
    """
    if not issubclass(BlueprintAlreadyRegisteredError, SemanticError):
        errmsg = "Expected BlueprintAlreadyRegisteredError to be a subclass of SemanticError"
        raise AssertionError(errmsg)

    return


def test_blueprint_already_registered_error_message_includes_class_name():
    """
        Test that the BlueprintAlreadyRegisteredError message includes the
        blueprint class name.
    """

    class MyItemsBlueprint:
        """
            A dummy blueprint class for testing.
        """
        pass

    error = BlueprintAlreadyRegisteredError(blueprint_cls=MyItemsBlueprint)
    error_message = str(error)

    if "MyItemsBlueprint" not in error_message:
        errmsg = (
            f"Expected error message to include class name 'MyItemsBlueprint'.\n"
            f"  Actual message: {error_message}"
        )
        raise AssertionError(errmsg)

    return


def test_blueprint_already_registered_error_stores_blueprint_cls():
    """
        Test that BlueprintAlreadyRegisteredError stores the blueprint_cls
        as an accessible attribute.
    """

    class SomeBlueprint:
        """
            A dummy blueprint class for testing.
        """
        pass

    error = BlueprintAlreadyRegisteredError(blueprint_cls=SomeBlueprint)

    if error.blueprint_cls is not SomeBlueprint:
        errmsg = (
            f"Expected blueprint_cls to be SomeBlueprint, "
            f"got {error.blueprint_cls}"
        )
        raise AssertionError(errmsg)

    return


# =============================================================================
# Unit Tests for EndpointConflictError
# =============================================================================

def test_endpoint_conflict_error_extends_semantic_error():
    """
        Test that EndpointConflictError is a subclass of SemanticError.
    """
    if not issubclass(EndpointConflictError, SemanticError):
        errmsg = "Expected EndpointConflictError to be a subclass of SemanticError"
        raise AssertionError(errmsg)

    return


def test_endpoint_conflict_error_message_includes_path_and_method():
    """
        Test that the EndpointConflictError message includes the path
        and HTTP method.
    """
    path = "/api/users"
    method = "POST"

    error = EndpointConflictError(path=path, method=method)
    error_message = str(error)

    if path not in error_message:
        errmsg = (
            f"Expected error message to include path '{path}'.\n"
            f"  Actual message: {error_message}"
        )
        raise AssertionError(errmsg)

    if method not in error_message:
        errmsg = (
            f"Expected error message to include method '{method}'.\n"
            f"  Actual message: {error_message}"
        )
        raise AssertionError(errmsg)

    return


def test_endpoint_conflict_error_message_includes_detail_when_provided():
    """
        Test that the EndpointConflictError message includes the detail
        string when one is provided.
    """
    path = "/api/items"
    method = "GET"
    detail = "handler 'get_items' already registered"

    error = EndpointConflictError(path=path, method=method, detail=detail)
    error_message = str(error)

    if detail not in error_message:
        errmsg = (
            f"Expected error message to include detail '{detail}'.\n"
            f"  Actual message: {error_message}"
        )
        raise AssertionError(errmsg)

    return


def test_endpoint_conflict_error_default_message_without_detail():
    """
        Test that the EndpointConflictError provides a default message
        when no detail is given.
    """
    path = "/api/orders"
    method = "DELETE"

    error = EndpointConflictError(path=path, method=method)
    error_message = str(error)

    if "already" not in error_message.lower():
        errmsg = (
            f"Expected default error message to mention 'already' registered.\n"
            f"  Actual message: {error_message}"
        )
        raise AssertionError(errmsg)

    return


def test_endpoint_conflict_error_stores_attributes():
    """
        Test that EndpointConflictError stores path, method, and detail
        as accessible attributes.
    """
    path = "/api/products"
    method = "PUT"
    detail = "duplicate route"

    error = EndpointConflictError(path=path, method=method, detail=detail)

    if error.path != path:
        errmsg = f"Expected path '{path}', got '{error.path}'"
        raise AssertionError(errmsg)

    if error.method != method:
        errmsg = f"Expected method '{method}', got '{error.method}'"
        raise AssertionError(errmsg)

    if error.detail != detail:
        errmsg = f"Expected detail '{detail}', got '{error.detail}'"
        raise AssertionError(errmsg)

    return


def test_endpoint_conflict_error_detail_defaults_to_none():
    """
        Test that EndpointConflictError detail attribute defaults to None
        when not provided.
    """
    error = EndpointConflictError(path="/api/test", method="GET")

    if error.detail is not None:
        errmsg = f"Expected detail to be None, got '{error.detail}'"
        raise AssertionError(errmsg)

    return
