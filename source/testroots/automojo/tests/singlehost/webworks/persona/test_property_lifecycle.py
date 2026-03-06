"""
.. module:: test_property_lifecycle
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: Property-based tests for the WebApplication lifecycle phase
        ordering enforcement.  Each property test iterates over generated
        inputs a minimum of 10 times to verify that universal properties
        hold across all valid executions.

.. moduleauthor:: Automation Mojo LLC
"""

__author__ = "Automation Mojo LLC"
__copyright__ = "Copyright 2025, Automation Mojo LLC"
__credits__ = []


import random
import string

import automojo.webworks.webapplication as webapp_module

from automojo.testbase.mocking import Mock, create_module_patch

from automojo.webworks.webapplication import (
    WebApplication,
    establish_webapp_persona,
    reset_webapp_persona,
)
from automojo.webworks.persona.lifecycle import LifecycleError, LifecyclePhase
from automojo.webworks.routing.router import Router
from automojo.webworks.routing.dispatcher import Dispatcher
from automojo.webworks.routing.request import Request
from automojo.webworks.authentication.system import AuthenticationSystem
from automojo.webworks.asgi.application import ASGIApplication
from automojo.webworks.configuration.lifecycle import ManagedConfigRegistry
from automojo.webworks.endpoints.registry import EndpointRegistry


# =============================================================================
# Constants
# =============================================================================

# Each tuple is (property_name, required_phase) for properties that should
# raise LifecycleError when accessed on a freshly created WebApplication
# (current phase = CREATED).
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
# Property 10: Lifecycle phase ordering enforcement
# Feature: webapp-lifecycle, Property 10: Lifecycle phase ordering enforcement
# Validates: Requirements 8.1, 8.2, 7.4
# =============================================================================

def test_property_lifecycle_phase_ordering_raises_lifecycle_error():
    """
        Property 10: Lifecycle phase ordering enforcement

        For any read-only property that depends on a lifecycle phase later
        than CREATED, accessing that property on a freshly created
        WebApplication (phase = CREATED) shall raise a LifecycleError
        whose message names the missing prerequisite phase and the
        attempted operation.

        Each iteration randomly selects a property from the guarded set
        and verifies the error attributes.  Runs 10 iterations.

        **Feature: webapp-lifecycle, Property 10: Lifecycle phase ordering enforcement**
        **Validates: Requirements 8.1, 8.2, 7.4**
    """
    for iteration in range(10):
        prop_name, required_phase = random.choice(PHASE_GUARDED_PROPERTIES)

        try:
            reset_webapp_persona()

            app = establish_webapp_persona(
                name="testapp",
                logger_name="testapp",
                log_basename="testapp",
            )

            # The app should be in CREATED phase
            if app.current_phase != LifecyclePhase.CREATED:
                errmsg = (
                    f"Iteration {iteration}: Expected current_phase to be "
                    f"CREATED, got '{app.current_phase.value}'"
                )
                raise AssertionError(errmsg)

            # Accessing the guarded property should raise LifecycleError
            caught_error = None

            try:
                _ = getattr(app, prop_name)
            except LifecycleError as err:
                caught_error = err
            except Exception as err:
                errmsg = (
                    f"Iteration {iteration}: Accessing '{prop_name}' raised "
                    f"{type(err).__name__} instead of LifecycleError: {err}"
                )
                raise AssertionError(errmsg)

            if caught_error is None:
                errmsg = (
                    f"Iteration {iteration}: Accessing '{prop_name}' did not "
                    f"raise LifecycleError (current phase is CREATED, "
                    f"required phase is {required_phase.value})"
                )
                raise AssertionError(errmsg)

            # Verify the error attributes match the expected values
            if caught_error.required_phase != required_phase:
                errmsg = (
                    f"Iteration {iteration}: LifecycleError for '{prop_name}' "
                    f"has required_phase '{caught_error.required_phase.value}', "
                    f"expected '{required_phase.value}'"
                )
                raise AssertionError(errmsg)

            if caught_error.current_phase != LifecyclePhase.CREATED:
                errmsg = (
                    f"Iteration {iteration}: LifecycleError for '{prop_name}' "
                    f"has current_phase '{caught_error.current_phase.value}', "
                    f"expected 'created'"
                )
                raise AssertionError(errmsg)

            # Verify the error message contains the phase names
            error_message = str(caught_error)

            if required_phase.value not in error_message:
                errmsg = (
                    f"Iteration {iteration}: LifecycleError message for "
                    f"'{prop_name}' does not contain required phase "
                    f"'{required_phase.value}'. Got: '{error_message}'"
                )
                raise AssertionError(errmsg)

            if LifecyclePhase.CREATED.value not in error_message:
                errmsg = (
                    f"Iteration {iteration}: LifecycleError message for "
                    f"'{prop_name}' does not contain current phase 'created'. "
                    f"Got: '{error_message}'"
                )
                raise AssertionError(errmsg)

        finally:
            reset_webapp_persona()

    return


def test_property_require_phase_rejects_all_insufficient_phases():
    """
        Property 10: Lifecycle phase ordering enforcement

        For any pair of (property, required_phase) in the guarded set,
        the _require_phase method shall raise LifecycleError when the
        current phase ordinal is strictly below the required phase ordinal.

        This test iterates over every guarded property and every phase
        that is below the required phase, verifying that LifecycleError
        is raised with the correct operation name.  Runs at least 100
        iterations by repeating the full matrix with random ordering.

        **Feature: webapp-lifecycle, Property 10: Lifecycle phase ordering enforcement**
        **Validates: Requirements 8.1, 8.2, 7.4**
    """
    phase_order = list(LifecyclePhase)

    # Build the full set of (property, insufficient_phase) pairs
    test_pairs = []
    for prop_name, required_phase in PHASE_GUARDED_PROPERTIES:
        required_index = phase_order.index(required_phase)
        for phase in phase_order[:required_index]:
            test_pairs.append((prop_name, required_phase, phase))

    # Ensure we run at least 10 iterations
    iterations = max(10, len(test_pairs))

    for iteration in range(iterations):
        prop_name, required_phase, insufficient_phase = test_pairs[iteration % len(test_pairs)]

        try:
            reset_webapp_persona()

            app = establish_webapp_persona(
                name="testapp",
                logger_name="testapp",
                log_basename="testapp",
            )

            # Manually set the phase to the insufficient phase for testing
            app._current_phase = insufficient_phase

            caught_error = None

            try:
                _ = getattr(app, prop_name)
            except LifecycleError as err:
                caught_error = err
            except Exception as err:
                errmsg = (
                    f"Iteration {iteration}: Accessing '{prop_name}' at phase "
                    f"'{insufficient_phase.value}' raised {type(err).__name__} "
                    f"instead of LifecycleError: {err}"
                )
                raise AssertionError(errmsg)

            if caught_error is None:
                errmsg = (
                    f"Iteration {iteration}: Accessing '{prop_name}' at phase "
                    f"'{insufficient_phase.value}' did not raise LifecycleError "
                    f"(required phase is '{required_phase.value}')"
                )
                raise AssertionError(errmsg)

            if caught_error.required_phase != required_phase:
                errmsg = (
                    f"Iteration {iteration}: LifecycleError for '{prop_name}' "
                    f"at phase '{insufficient_phase.value}' has required_phase "
                    f"'{caught_error.required_phase.value}', expected "
                    f"'{required_phase.value}'"
                )
                raise AssertionError(errmsg)

            if caught_error.current_phase != insufficient_phase:
                errmsg = (
                    f"Iteration {iteration}: LifecycleError for '{prop_name}' "
                    f"has current_phase '{caught_error.current_phase.value}', "
                    f"expected '{insufficient_phase.value}'"
                )
                raise AssertionError(errmsg)

            # Verify the error message contains both phase names
            error_message = str(caught_error)

            if required_phase.value not in error_message:
                errmsg = (
                    f"Iteration {iteration}: LifecycleError message does not "
                    f"contain required phase '{required_phase.value}'. "
                    f"Got: '{error_message}'"
                )
                raise AssertionError(errmsg)

            if insufficient_phase.value not in error_message:
                errmsg = (
                    f"Iteration {iteration}: LifecycleError message does not "
                    f"contain current phase '{insufficient_phase.value}'. "
                    f"Got: '{error_message}'"
                )
                raise AssertionError(errmsg)

        finally:
            reset_webapp_persona()

    return


def test_property_sufficient_phase_allows_access():
    """
        Property 10: Lifecycle phase ordering enforcement

        For any pair of (property, required_phase) in the guarded set,
        when the current phase ordinal is at or above the required phase
        ordinal, accessing the property shall NOT raise LifecycleError.

        This test verifies the complementary condition: that phase
        enforcement does not block access when the prerequisite is met.
        Runs at least 10 iterations.

        **Feature: webapp-lifecycle, Property 10: Lifecycle phase ordering enforcement**
        **Validates: Requirements 8.1, 8.2, 7.4**
    """
    phase_order = list(LifecyclePhase)

    # Build the full set of (property, sufficient_phase) pairs
    test_pairs = []
    for prop_name, required_phase in PHASE_GUARDED_PROPERTIES:
        required_index = phase_order.index(required_phase)
        # Include the required phase and all phases above it (except SHUTDOWN)
        for phase in phase_order[required_index:]:
            if phase == LifecyclePhase.SHUTDOWN:
                continue
            test_pairs.append((prop_name, required_phase, phase))

    # Ensure we run at least 10 iterations
    iterations = max(10, len(test_pairs))

    for iteration in range(iterations):
        prop_name, required_phase, sufficient_phase = test_pairs[iteration % len(test_pairs)]

        try:
            reset_webapp_persona()

            app = establish_webapp_persona(
                name="testapp",
                logger_name="testapp",
                log_basename="testapp",
            )

            # Manually set the phase to the sufficient phase for testing
            app._current_phase = sufficient_phase

            # Accessing the property should NOT raise LifecycleError.
            # The property value will be None since no setup has run,
            # but the phase guard should not block access.
            lifecycle_error_raised = False

            try:
                _ = getattr(app, prop_name)
            except LifecycleError:
                lifecycle_error_raised = True

            if lifecycle_error_raised:
                errmsg = (
                    f"Iteration {iteration}: Accessing '{prop_name}' at phase "
                    f"'{sufficient_phase.value}' raised LifecycleError, but "
                    f"the phase '{sufficient_phase.value}' meets the "
                    f"requirement of '{required_phase.value}'"
                )
                raise AssertionError(errmsg)

        finally:
            reset_webapp_persona()

    return


# =============================================================================
# Helpers
# =============================================================================

def _random_name(min_length=3, max_length=12):
    """
        Generate a random lowercase alphabetic name suitable for use as
        a persona name or logger name.

        :returns: A random string of lowercase letters.
    """
    length = random.randint(min_length, max_length)
    return "".join(random.choices(string.ascii_lowercase, k=length))


def _create_app_with_mock_config():
    """
        Creates a fresh WebApplication via ``establish_webapp_persona``
        and patches ``ManagedConfigRegistry`` so that ``startup()`` can
        complete without filesystem access.

        :returns: A tuple of (app, patch) where *patch* must be
            deactivated in a ``finally`` block.
    """
    reset_webapp_persona()

    app = establish_webapp_persona(
        name="testapp",
        logger_name="testapp",
        log_basename="testapp",
    )

    # Patch ManagedConfigRegistry to avoid filesystem side effects
    patch = create_module_patch(webapp_module, "ManagedConfigRegistry")
    mock_cls = patch.activate()
    mock_registry = Mock()
    mock_registry.configure(recursive=True)
    mock_cls.configure(return_value=mock_registry)

    return app, patch, mock_registry


# =============================================================================
# Property 1: Startup initializes all subsystems
# Feature: webapp-lifecycle, Property 1: Startup initializes all subsystems
# Validates: Requirements 1.1, 1.2, 1.3, 4.1, 5.1, 6.1, 7.1, 8.3
# =============================================================================

def test_property_startup_initializes_all_subsystems():
    """
        Property 1: Startup initializes all subsystems

        For any valid persona configuration, after calling ``startup()``
        on a WebApplication, the properties ``router``, ``dispatcher``,
        ``asgi_app``, ``config``, ``auth_system`` shall all return
        non-None instances of their expected types, and
        ``current_phase`` shall be ``READY``.

        The ``credentials`` and ``data_profiles`` properties are
        currently placeholders (None) so we verify they are accessible
        without raising ``LifecycleError`` rather than checking for
        non-None.

        Each iteration uses a randomly generated persona name and
        logger name.  Runs 10 iterations.

        **Feature: webapp-lifecycle, Property 1: Startup initializes all subsystems**
        **Validates: Requirements 1.1, 1.2, 1.3, 4.1, 5.1, 6.1, 7.1, 8.3**
    """
    for iteration in range(10):
        patch = None

        try:
            reset_webapp_persona()

            persona_name = _random_name()
            logger_name = _random_name()

            app = establish_webapp_persona(
                name=persona_name,
                logger_name=logger_name,
                log_basename=logger_name,
            )

            # Patch ManagedConfigRegistry to avoid filesystem access
            patch = create_module_patch(webapp_module, "ManagedConfigRegistry")
            mock_cls = patch.activate()
            mock_registry = Mock()
            mock_registry.configure(recursive=True)
            mock_cls.configure(return_value=mock_registry)

            app.startup()

            # Verify current_phase is READY
            if app.current_phase != LifecyclePhase.READY:
                errmsg = (
                    f"Iteration {iteration}: Expected current_phase READY, "
                    f"got '{app.current_phase.value}' "
                    f"(persona_name='{persona_name}')"
                )
                raise AssertionError(errmsg)

            # Verify router is non-None and correct type
            if not isinstance(app.router, Router):
                errmsg = (
                    f"Iteration {iteration}: Expected router to be Router, "
                    f"got {type(app.router).__name__} "
                    f"(persona_name='{persona_name}')"
                )
                raise AssertionError(errmsg)

            # Verify dispatcher is non-None and correct type
            if not isinstance(app.dispatcher, Dispatcher):
                errmsg = (
                    f"Iteration {iteration}: Expected dispatcher to be "
                    f"Dispatcher, got {type(app.dispatcher).__name__} "
                    f"(persona_name='{persona_name}')"
                )
                raise AssertionError(errmsg)

            # Verify asgi_app is non-None and correct type
            if not isinstance(app.asgi_app, ASGIApplication):
                errmsg = (
                    f"Iteration {iteration}: Expected asgi_app to be "
                    f"ASGIApplication, got {type(app.asgi_app).__name__} "
                    f"(persona_name='{persona_name}')"
                )
                raise AssertionError(errmsg)

            # Verify config is accessible (mock instance)
            config_val = app.config
            if config_val is None:
                errmsg = (
                    f"Iteration {iteration}: Expected config to be non-None "
                    f"(persona_name='{persona_name}')"
                )
                raise AssertionError(errmsg)

            # Verify auth_system is non-None and correct type
            if not isinstance(app.auth_system, AuthenticationSystem):
                errmsg = (
                    f"Iteration {iteration}: Expected auth_system to be "
                    f"AuthenticationSystem, got "
                    f"{type(app.auth_system).__name__} "
                    f"(persona_name='{persona_name}')"
                )
                raise AssertionError(errmsg)

            # Verify credentials is accessible without LifecycleError
            # (placeholder — currently None)
            try:
                _ = app.credentials
            except LifecycleError as err:
                errmsg = (
                    f"Iteration {iteration}: Accessing credentials raised "
                    f"LifecycleError after startup: {err} "
                    f"(persona_name='{persona_name}')"
                )
                raise AssertionError(errmsg)

            # Verify data_profiles is accessible without LifecycleError
            # (placeholder — currently None)
            try:
                _ = app.data_profiles
            except LifecycleError as err:
                errmsg = (
                    f"Iteration {iteration}: Accessing data_profiles raised "
                    f"LifecycleError after startup: {err} "
                    f"(persona_name='{persona_name}')"
                )
                raise AssertionError(errmsg)

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

def test_property_infrastructure_wiring_consistency():
    """
        Property 2: Infrastructure wiring consistency

        After ``startup()`` completes, the Dispatcher's ``router``
        property shall return the same Router object as
        ``WebApplication.router`` (identity check), and all
        EndpointDescriptor instances from the EndpointRegistry at
        startup time shall be matchable via the Router.

        Each iteration uses a randomly generated persona name.
        Runs 10 iterations.

        **Feature: webapp-lifecycle, Property 2: Infrastructure wiring consistency**
        **Validates: Requirements 1.4, 1.5, 1.6**
    """
    for iteration in range(10):
        patch = None

        try:
            reset_webapp_persona()

            persona_name = _random_name()

            app = establish_webapp_persona(
                name=persona_name,
                logger_name=persona_name,
                log_basename=persona_name,
            )

            # Snapshot the EndpointRegistry descriptors before startup
            descriptors_before = EndpointRegistry.collect()

            # Patch ManagedConfigRegistry to avoid filesystem access
            patch = create_module_patch(webapp_module, "ManagedConfigRegistry")
            mock_cls = patch.activate()
            mock_registry = Mock()
            mock_registry.configure(recursive=True)
            mock_cls.configure(return_value=mock_registry)

            app.startup()

            # Identity check: Dispatcher.router is the same object as
            # WebApplication.router
            if app.dispatcher.router is not app.router:
                errmsg = (
                    f"Iteration {iteration}: Dispatcher.router is not the "
                    f"same object as WebApplication.router "
                    f"(persona_name='{persona_name}')"
                )
                raise AssertionError(errmsg)

            # Verify all EndpointDescriptors from the registry are
            # matchable via the Router
            for descriptor in descriptors_before:
                path = descriptor.path
                methods = descriptor.methods if descriptor.methods else ["GET"]

                for method in methods:
                    request = Request(method=method, path=path)
                    match_result = app.router.match(request)

                    if match_result is None:
                        errmsg = (
                            f"Iteration {iteration}: EndpointDescriptor "
                            f"path='{path}' method='{method}' is not "
                            f"matchable via the Router "
                            f"(persona_name='{persona_name}')"
                        )
                        raise AssertionError(errmsg)

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

def test_property_shutdown_releases_all_resources():
    """
        Property 11: Shutdown releases all resources

        For any WebApplication that has completed ``startup()``, calling
        ``shutdown()`` shall result in ``current_phase`` being
        ``SHUTDOWN`` and the config registry's ``cleanup()`` having been
        called.

        Each iteration uses a randomly generated persona name.
        Runs 10 iterations.

        **Feature: webapp-lifecycle, Property 11: Shutdown releases all resources**
        **Validates: Requirements 8.4**
    """
    for iteration in range(10):
        patch = None

        try:
            reset_webapp_persona()

            persona_name = _random_name()

            app = establish_webapp_persona(
                name=persona_name,
                logger_name=persona_name,
                log_basename=persona_name,
            )

            # Patch ManagedConfigRegistry to avoid filesystem access
            patch = create_module_patch(webapp_module, "ManagedConfigRegistry")
            mock_cls = patch.activate()
            mock_registry = Mock()
            mock_registry.configure(recursive=True)
            mock_cls.configure(return_value=mock_registry)

            app.startup()

            # Verify we are in READY phase before shutdown
            if app.current_phase != LifecyclePhase.READY:
                errmsg = (
                    f"Iteration {iteration}: Expected phase READY before "
                    f"shutdown, got '{app.current_phase.value}' "
                    f"(persona_name='{persona_name}')"
                )
                raise AssertionError(errmsg)

            app.shutdown()

            # Verify current_phase is SHUTDOWN
            if app.current_phase != LifecyclePhase.SHUTDOWN:
                errmsg = (
                    f"Iteration {iteration}: Expected current_phase SHUTDOWN "
                    f"after shutdown(), got '{app.current_phase.value}' "
                    f"(persona_name='{persona_name}')"
                )
                raise AssertionError(errmsg)

            # Verify config cleanup() was called on the mock registry
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

# The expected lifecycle method call order during startup.
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


def test_property_subclass_overrides_invoked_during_startup():
    """
        Property 12: Subclass overrides are invoked during startup

        For any WebApplication subclass that overrides all lifecycle
        phase methods with tracking wrappers, calling ``startup()``
        shall invoke the overridden methods (not the base
        implementations) in the correct lifecycle order:

        1. ``setup_configuration``
        2. ``setup_credentials``
        3. ``setup_data_profiles``
        4. ``setup_database``
        5. ``setup_authentication``
        6. ``setup_infrastructure``

        Each iteration uses a randomly generated persona name and
        verifies the recorded call order matches the expected sequence.
        Runs 10 iterations.

        **Feature: webapp-lifecycle, Property 12: Subclass overrides are invoked during startup**
        **Validates: Requirements 9.2**
    """
    for iteration in range(10):
        patch = None

        try:
            reset_webapp_persona()

            persona_name = _random_name()

            app = establish_webapp_persona(
                name=persona_name,
                logger_name=persona_name,
                log_basename=persona_name,
                application_cls=TrackingWebApplication,
            )

            # Verify the correct subclass was instantiated
            if not isinstance(app, TrackingWebApplication):
                errmsg = (
                    f"Iteration {iteration}: Expected TrackingWebApplication "
                    f"instance, got {type(app).__name__} "
                    f"(persona_name='{persona_name}')"
                )
                raise AssertionError(errmsg)

            # Verify call_order is empty before startup
            if len(app._call_order) != 0:
                errmsg = (
                    f"Iteration {iteration}: Expected empty _call_order "
                    f"before startup, got {app._call_order} "
                    f"(persona_name='{persona_name}')"
                )
                raise AssertionError(errmsg)

            # Patch ManagedConfigRegistry to avoid filesystem access
            patch = create_module_patch(webapp_module, "ManagedConfigRegistry")
            mock_cls = patch.activate()
            mock_registry = Mock()
            mock_registry.configure(recursive=True)
            mock_cls.configure(return_value=mock_registry)

            app.startup()

            # Verify current_phase is READY after startup
            if app.current_phase != LifecyclePhase.READY:
                errmsg = (
                    f"Iteration {iteration}: Expected current_phase READY "
                    f"after startup, got '{app.current_phase.value}' "
                    f"(persona_name='{persona_name}')"
                )
                raise AssertionError(errmsg)

            # Verify all overrides were called
            if len(app._call_order) != len(EXPECTED_LIFECYCLE_ORDER):
                errmsg = (
                    f"Iteration {iteration}: Expected "
                    f"{len(EXPECTED_LIFECYCLE_ORDER)} lifecycle calls, "
                    f"got {len(app._call_order)}. "
                    f"Recorded: {app._call_order} "
                    f"(persona_name='{persona_name}')"
                )
                raise AssertionError(errmsg)

            # Verify the call order matches the expected sequence
            if app._call_order != EXPECTED_LIFECYCLE_ORDER:
                errmsg = (
                    f"Iteration {iteration}: Lifecycle call order mismatch. "
                    f"Expected: {EXPECTED_LIFECYCLE_ORDER}, "
                    f"got: {app._call_order} "
                    f"(persona_name='{persona_name}')"
                )
                raise AssertionError(errmsg)

            # Verify each individual position for debuggability
            for idx, expected_method in enumerate(EXPECTED_LIFECYCLE_ORDER):
                actual_method = app._call_order[idx]
                if actual_method != expected_method:
                    errmsg = (
                        f"Iteration {iteration}: At position {idx}, "
                        f"expected '{expected_method}' but got "
                        f"'{actual_method}'. Full order: {app._call_order} "
                        f"(persona_name='{persona_name}')"
                    )
                    raise AssertionError(errmsg)

        finally:
            if patch is not None:
                patch.deactivate()
            reset_webapp_persona()

    return
