"""
.. module:: test_property_lifecycle
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: Property-based tests for the WebApplication lifecycle phase
        ordering enforcement.  Each property test uses the testbase
        ``@given`` decorator to verify that universal properties hold across
        generated inputs.

.. moduleauthor:: Code Craft AI LLC
"""

__author__ = "Code Craft AI LLC"
__copyright__ = "Copyright 2025, Code Craft AI LLC"
__credits__ = []

import ccai.testbase as testbase

from ccai.testbase.properties import given
from ccai.testbase.properties import strategies as st

from ccai.testbase.mocking import Mock, create_module_patch

import ccai.webworks.webapplication as webapp_module

from ccai.webworks.webapplication import (
    WebApplication,
    establish_webapp_persona,
    reset_webapp_persona,
)
from ccai.webworks.persona.lifecycle import LifecycleError, LifecyclePhase
from ccai.webworks.routing.router import Router
from ccai.webworks.routing.dispatcher import Dispatcher
from ccai.webworks.routing.request import Request
from ccai.webworks.authentication.system import AuthenticationSystem
from ccai.webworks.asgi.application import ASGIApplication
from ccai.webworks.endpoints.registry import EndpointRegistry


# =============================================================================
# Constants
# =============================================================================

PHASE_GUARDED_PROPERTIES = [
    ("router", LifecyclePhase.INFRASTRUCTURE_READY),
    ("dispatcher", LifecyclePhase.INFRASTRUCTURE_READY),
    ("asgi_app", LifecyclePhase.INFRASTRUCTURE_READY),
    ("config", LifecyclePhase.CONFIGURED),
    ("credentials", LifecyclePhase.CREDENTIALS_LOADED),
    ("data_profiles", LifecyclePhase.DATA_PROFILES_LOADED),
    ("auth_system", LifecyclePhase.AUTHENTICATION_READY),
]


# =============================================================================
# Strategies
# =============================================================================

name_strategy = st.text(
    alphabet="abcdefghijklmnopqrstuvwxyz",
    min_size=3,
    max_size=12,
)

guarded_property_strategy = st.sampled_from(PHASE_GUARDED_PROPERTIES)

# Build the full set of (property, required_phase, insufficient_phase) tuples
_phase_order = list(LifecyclePhase)
_insufficient_phase_pairs = []
for _prop_name, _required_phase in PHASE_GUARDED_PROPERTIES:
    _required_index = _phase_order.index(_required_phase)
    for _phase in _phase_order[:_required_index]:
        _insufficient_phase_pairs.append((_prop_name, _required_phase, _phase))

insufficient_phase_strategy = st.sampled_from(_insufficient_phase_pairs)

# Build the full set of (property, required_phase, sufficient_phase) tuples
_sufficient_phase_pairs = []
for _prop_name, _required_phase in PHASE_GUARDED_PROPERTIES:
    _required_index = _phase_order.index(_required_phase)
    for _phase in _phase_order[_required_index:]:
        if _phase == LifecyclePhase.SHUTDOWN:
            continue
        _sufficient_phase_pairs.append((_prop_name, _required_phase, _phase))

sufficient_phase_strategy = st.sampled_from(_sufficient_phase_pairs)


# =============================================================================
# Property 10: Lifecycle phase ordering enforcement
# Feature: webapp-lifecycle, Property 10: Lifecycle phase ordering enforcement
# Validates: Requirements 8.1, 8.2, 7.4
# =============================================================================

@given(
    guarded_prop=guarded_property_strategy,
    constraints={"max_examples": 10},
)
def test_property_lifecycle_phase_ordering_raises_lifecycle_error(guarded_prop):
    """
        Property 10: Lifecycle phase ordering enforcement

        For any read-only property that depends on a lifecycle phase later
        than CREATED, accessing that property on a freshly created
        WebApplication (phase = CREATED) shall raise a LifecycleError
        whose message names the missing prerequisite phase and the
        attempted operation.

        **Feature: webapp-lifecycle, Property 10: Lifecycle phase ordering enforcement**
        **Validates: Requirements 8.1, 8.2, 7.4**
    """
    prop_name, required_phase = guarded_prop

    try:
        reset_webapp_persona()

        app = establish_webapp_persona(
            name="testapp",
            logger_name="testapp",
            log_basename="testapp",
        )

        testbase.assert_equal(
            app.current_phase, LifecyclePhase.CREATED,
            f"Expected current_phase to be CREATED, got '{app.current_phase.value}'"
        )

        caught_error = None

        try:
            _ = getattr(app, prop_name)
        except LifecycleError as err:
            caught_error = err
        except Exception as err:
            raise AssertionError(
                f"Accessing '{prop_name}' raised {type(err).__name__} "
                f"instead of LifecycleError: {err}"
            )

        testbase.assert_true(
            caught_error is not None,
            f"Accessing '{prop_name}' did not raise LifecycleError "
            f"(current phase is CREATED, required phase is {required_phase.value})"
        )

        testbase.assert_equal(
            caught_error.required_phase, required_phase,
            f"LifecycleError for '{prop_name}' has required_phase "
            f"'{caught_error.required_phase.value}', expected '{required_phase.value}'"
        )

        testbase.assert_equal(
            caught_error.current_phase, LifecyclePhase.CREATED,
            f"LifecycleError for '{prop_name}' has current_phase "
            f"'{caught_error.current_phase.value}', expected 'created'"
        )

        error_message = str(caught_error)

        testbase.assert_true(
            required_phase.value in error_message,
            f"LifecycleError message for '{prop_name}' does not contain "
            f"required phase '{required_phase.value}'. Got: '{error_message}'"
        )

        testbase.assert_true(
            LifecyclePhase.CREATED.value in error_message,
            f"LifecycleError message for '{prop_name}' does not contain "
            f"current phase 'created'. Got: '{error_message}'"
        )

    finally:
        reset_webapp_persona()

    return


@given(
    pair=insufficient_phase_strategy,
    constraints={"max_examples": 100},
)
def test_property_require_phase_rejects_all_insufficient_phases(pair):
    """
        Property 10: Lifecycle phase ordering enforcement

        For any pair of (property, required_phase) in the guarded set,
        the _require_phase method shall raise LifecycleError when the
        current phase ordinal is strictly below the required phase ordinal.

        **Feature: webapp-lifecycle, Property 10: Lifecycle phase ordering enforcement**
        **Validates: Requirements 8.1, 8.2, 7.4**
    """
    prop_name, required_phase, insufficient_phase = pair

    try:
        reset_webapp_persona()

        app = establish_webapp_persona(
            name="testapp",
            logger_name="testapp",
            log_basename="testapp",
        )

        app._current_phase = insufficient_phase

        caught_error = None

        try:
            _ = getattr(app, prop_name)
        except LifecycleError as err:
            caught_error = err
        except Exception as err:
            raise AssertionError(
                f"Accessing '{prop_name}' at phase '{insufficient_phase.value}' "
                f"raised {type(err).__name__} instead of LifecycleError: {err}"
            )

        testbase.assert_true(
            caught_error is not None,
            f"Accessing '{prop_name}' at phase '{insufficient_phase.value}' "
            f"did not raise LifecycleError (required phase is '{required_phase.value}')"
        )

        testbase.assert_equal(
            caught_error.required_phase, required_phase,
            f"LifecycleError for '{prop_name}' at phase '{insufficient_phase.value}' "
            f"has required_phase '{caught_error.required_phase.value}', "
            f"expected '{required_phase.value}'"
        )

        testbase.assert_equal(
            caught_error.current_phase, insufficient_phase,
            f"LifecycleError for '{prop_name}' has current_phase "
            f"'{caught_error.current_phase.value}', expected '{insufficient_phase.value}'"
        )

        error_message = str(caught_error)

        testbase.assert_true(
            required_phase.value in error_message,
            f"LifecycleError message does not contain required phase "
            f"'{required_phase.value}'. Got: '{error_message}'"
        )

        testbase.assert_true(
            insufficient_phase.value in error_message,
            f"LifecycleError message does not contain current phase "
            f"'{insufficient_phase.value}'. Got: '{error_message}'"
        )

    finally:
        reset_webapp_persona()

    return


@given(
    pair=sufficient_phase_strategy,
    constraints={"max_examples": 100},
)
def test_property_sufficient_phase_allows_access(pair):
    """
        Property 10: Lifecycle phase ordering enforcement

        For any pair of (property, required_phase) in the guarded set,
        when the current phase ordinal is at or above the required phase
        ordinal, accessing the property shall NOT raise LifecycleError.

        **Feature: webapp-lifecycle, Property 10: Lifecycle phase ordering enforcement**
        **Validates: Requirements 8.1, 8.2, 7.4**
    """
    prop_name, required_phase, sufficient_phase = pair

    try:
        reset_webapp_persona()

        app = establish_webapp_persona(
            name="testapp",
            logger_name="testapp",
            log_basename="testapp",
        )

        app._current_phase = sufficient_phase

        lifecycle_error_raised = False

        try:
            _ = getattr(app, prop_name)
        except LifecycleError:
            lifecycle_error_raised = True

        testbase.assert_false(
            lifecycle_error_raised,
            f"Accessing '{prop_name}' at phase '{sufficient_phase.value}' "
            f"raised LifecycleError, but the phase '{sufficient_phase.value}' "
            f"meets the requirement of '{required_phase.value}'"
        )

    finally:
        reset_webapp_persona()

    return


# =============================================================================
# Property 1: Startup initializes all subsystems
# Feature: webapp-lifecycle, Property 1: Startup initializes all subsystems
# Validates: Requirements 1.1, 1.2, 1.3, 4.1, 5.1, 6.1, 7.1, 8.3
# =============================================================================

@given(
    persona_name=name_strategy,
    constraints={"max_examples": 10},
)
def test_property_startup_initializes_all_subsystems(persona_name):
    """
        Property 1: Startup initializes all subsystems

        For any valid persona configuration, after calling ``startup()``
        on a WebApplication, the properties ``router``, ``dispatcher``,
        ``asgi_app``, ``config``, ``auth_system`` shall all return
        non-None instances of their expected types, and
        ``current_phase`` shall be ``READY``.

        **Feature: webapp-lifecycle, Property 1: Startup initializes all subsystems**
        **Validates: Requirements 1.1, 1.2, 1.3, 4.1, 5.1, 6.1, 7.1, 8.3**
    """
    patch = None

    try:
        reset_webapp_persona()

        app = establish_webapp_persona(
            name=persona_name,
            logger_name=persona_name,
            log_basename=persona_name,
        )

        patch = create_module_patch(webapp_module, "ManagedConfigRegistry")
        mock_cls = patch.activate()
        mock_registry = Mock()
        mock_registry.configure(recursive=True)
        mock_cls.configure(return_value=mock_registry)

        app.startup()

        testbase.assert_equal(
            app.current_phase, LifecyclePhase.READY,
            f"Expected current_phase READY, got '{app.current_phase.value}' "
            f"(persona_name='{persona_name}')"
        )

        testbase.assert_true(
            isinstance(app.router, Router),
            f"Expected router to be Router, got {type(app.router).__name__} "
            f"(persona_name='{persona_name}')"
        )

        testbase.assert_true(
            isinstance(app.dispatcher, Dispatcher),
            f"Expected dispatcher to be Dispatcher, got {type(app.dispatcher).__name__} "
            f"(persona_name='{persona_name}')"
        )

        testbase.assert_true(
            isinstance(app.asgi_app, ASGIApplication),
            f"Expected asgi_app to be ASGIApplication, got {type(app.asgi_app).__name__} "
            f"(persona_name='{persona_name}')"
        )

        testbase.assert_true(
            app.config is not None,
            f"Expected config to be non-None (persona_name='{persona_name}')"
        )

        testbase.assert_true(
            isinstance(app.auth_system, AuthenticationSystem),
            f"Expected auth_system to be AuthenticationSystem, got "
            f"{type(app.auth_system).__name__} (persona_name='{persona_name}')"
        )

        # Verify credentials is accessible without LifecycleError (placeholder — currently None)
        try:
            _ = app.credentials
        except LifecycleError as err:
            raise AssertionError(
                f"Accessing credentials raised LifecycleError after startup: {err} "
                f"(persona_name='{persona_name}')"
            )

        # Verify data_profiles is accessible without LifecycleError (placeholder — currently None)
        try:
            _ = app.data_profiles
        except LifecycleError as err:
            raise AssertionError(
                f"Accessing data_profiles raised LifecycleError after startup: {err} "
                f"(persona_name='{persona_name}')"
            )

    finally:
        if patch is not None:
            patch.deactivate()
        reset_webapp_persona()

    return


# =============================================================================
# Property 2: Infrastructure wiring consistency
# Feature: webapp-lifecycle, Property 2: Infrastructure wiring consistency
# Validates: Requirements 1.4, 1.5, 1.6
# =============================================================================

@given(
    persona_name=name_strategy,
    constraints={"max_examples": 10},
)
def test_property_infrastructure_wiring_consistency(persona_name):
    """
        Property 2: Infrastructure wiring consistency

        After ``startup()`` completes, the Dispatcher's ``router``
        property shall return the same Router object as
        ``WebApplication.router`` (identity check), and all
        EndpointDescriptor instances from the EndpointRegistry at
        startup time shall be matchable via the Router.

        **Feature: webapp-lifecycle, Property 2: Infrastructure wiring consistency**
        **Validates: Requirements 1.4, 1.5, 1.6**
    """
    registry = EndpointRegistry()
    patch = None

    try:
        reset_webapp_persona()

        app = establish_webapp_persona(
            name=persona_name,
            logger_name=persona_name,
            log_basename=persona_name,
        )

        descriptors_before = registry.collect()

        patch = create_module_patch(webapp_module, "ManagedConfigRegistry")
        mock_cls = patch.activate()
        mock_registry = Mock()
        mock_registry.configure(recursive=True)
        mock_cls.configure(return_value=mock_registry)

        app.startup()

        testbase.assert_true(
            app.dispatcher.router is app.router,
            f"Dispatcher.router is not the same object as WebApplication.router "
            f"(persona_name='{persona_name}')"
        )

        for descriptor in descriptors_before:
            path = descriptor.path
            methods = descriptor.methods if descriptor.methods else ["GET"]

            for method in methods:
                request = Request(method=method, path=path)
                match_result = app.router.match(request)

                testbase.assert_true(
                    match_result is not None,
                    f"EndpointDescriptor path='{path}' method='{method}' is not "
                    f"matchable via the Router (persona_name='{persona_name}')"
                )

    finally:
        if patch is not None:
            patch.deactivate()
        reset_webapp_persona()

    return


# =============================================================================
# Property 11: Shutdown releases all resources
# Feature: webapp-lifecycle, Property 11: Shutdown releases all resources
# Validates: Requirements 8.4
# =============================================================================

@given(
    persona_name=name_strategy,
    constraints={"max_examples": 10},
)
def test_property_shutdown_releases_all_resources(persona_name):
    """
        Property 11: Shutdown releases all resources

        For any WebApplication that has completed ``startup()``, calling
        ``shutdown()`` shall result in ``current_phase`` being
        ``SHUTDOWN`` and the config registry's ``cleanup()`` having been
        called.

        **Feature: webapp-lifecycle, Property 11: Shutdown releases all resources**
        **Validates: Requirements 8.4**
    """
    patch = None

    try:
        reset_webapp_persona()

        app = establish_webapp_persona(
            name=persona_name,
            logger_name=persona_name,
            log_basename=persona_name,
        )

        patch = create_module_patch(webapp_module, "ManagedConfigRegistry")
        mock_cls = patch.activate()
        mock_registry = Mock()
        mock_registry.configure(recursive=True)
        mock_cls.configure(return_value=mock_registry)

        app.startup()

        testbase.assert_equal(
            app.current_phase, LifecyclePhase.READY,
            f"Expected phase READY before shutdown, got '{app.current_phase.value}' "
            f"(persona_name='{persona_name}')"
        )

        app.shutdown()

        testbase.assert_equal(
            app.current_phase, LifecyclePhase.SHUTDOWN,
            f"Expected current_phase SHUTDOWN after shutdown(), "
            f"got '{app.current_phase.value}' (persona_name='{persona_name}')"
        )

        cleanup_mock = mock_registry.cleanup
        cleanup_mock.mock_context().assert_called()

    finally:
        if patch is not None:
            patch.deactivate()
        reset_webapp_persona()

    return


# =============================================================================
# Property 12: Subclass overrides are invoked during startup
# Feature: webapp-lifecycle, Property 12: Subclass overrides are invoked
#     during startup
# Validates: Requirements 9.2
# =============================================================================

EXPECTED_LIFECYCLE_ORDER = [
    "setup_configuration",
    "setup_credentials",
    "setup_data_profiles",
    "setup_database",
    "setup_authentication",
    "setup_infrastructure",
]


class TrackingWebApplication(WebApplication):
    """
        A WebApplication subclass that overrides every lifecycle phase
        method with a tracking wrapper.  Each override records the
        method name in ``_call_order`` before delegating to the base
        implementation via ``super()``.
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._call_order: list = []
        return

    def setup_configuration(self) -> None:
        self._call_order.append("setup_configuration")
        super().setup_configuration()
        return

    def setup_credentials(self) -> None:
        self._call_order.append("setup_credentials")
        super().setup_credentials()
        return

    def setup_data_profiles(self) -> None:
        self._call_order.append("setup_data_profiles")
        super().setup_data_profiles()
        return

    def setup_database(self) -> None:
        self._call_order.append("setup_database")
        super().setup_database()
        return

    def setup_authentication(self) -> None:
        self._call_order.append("setup_authentication")
        super().setup_authentication()
        return

    def setup_infrastructure(self) -> None:
        self._call_order.append("setup_infrastructure")
        super().setup_infrastructure()
        return


@given(
    persona_name=name_strategy,
    constraints={"max_examples": 10},
)
def test_property_subclass_overrides_invoked_during_startup(persona_name):
    """
        Property 12: Subclass overrides are invoked during startup

        For any WebApplication subclass that overrides all lifecycle
        phase methods with tracking wrappers, calling ``startup()``
        shall invoke the overridden methods in the correct lifecycle order.

        **Feature: webapp-lifecycle, Property 12: Subclass overrides are invoked during startup**
        **Validates: Requirements 9.2**
    """
    patch = None

    try:
        reset_webapp_persona()

        app = establish_webapp_persona(
            name=persona_name,
            logger_name=persona_name,
            log_basename=persona_name,
            application_cls=TrackingWebApplication,
        )

        testbase.assert_true(
            isinstance(app, TrackingWebApplication),
            f"Expected TrackingWebApplication instance, got {type(app).__name__} "
            f"(persona_name='{persona_name}')"
        )

        testbase.assert_equal(
            len(app._call_order), 0,
            f"Expected empty _call_order before startup, got {app._call_order} "
            f"(persona_name='{persona_name}')"
        )

        patch = create_module_patch(webapp_module, "ManagedConfigRegistry")
        mock_cls = patch.activate()
        mock_registry = Mock()
        mock_registry.configure(recursive=True)
        mock_cls.configure(return_value=mock_registry)

        app.startup()

        testbase.assert_equal(
            app.current_phase, LifecyclePhase.READY,
            f"Expected current_phase READY after startup, "
            f"got '{app.current_phase.value}' (persona_name='{persona_name}')"
        )

        testbase.assert_equal(
            len(app._call_order), len(EXPECTED_LIFECYCLE_ORDER),
            f"Expected {len(EXPECTED_LIFECYCLE_ORDER)} lifecycle calls, "
            f"got {len(app._call_order)}. Recorded: {app._call_order} "
            f"(persona_name='{persona_name}')"
        )

        testbase.assert_equal(
            app._call_order, EXPECTED_LIFECYCLE_ORDER,
            f"Lifecycle call order mismatch. Expected: {EXPECTED_LIFECYCLE_ORDER}, "
            f"got: {app._call_order} (persona_name='{persona_name}')"
        )

        for idx, expected_method in enumerate(EXPECTED_LIFECYCLE_ORDER):
            actual_method = app._call_order[idx]
            testbase.assert_equal(
                actual_method, expected_method,
                f"At position {idx}, expected '{expected_method}' but got "
                f"'{actual_method}'. Full order: {app._call_order} "
                f"(persona_name='{persona_name}')"
            )

    finally:
        if patch is not None:
            patch.deactivate()
        reset_webapp_persona()

    return


if __name__ == "__main__":
    from ccai.testbase.entrypoints import generic_test_entrypoint
    generic_test_entrypoint()
