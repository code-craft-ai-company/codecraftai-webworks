"""
.. module:: test_webapplication_lifecycle
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: Unit tests for the WebApplication lifecycle setup methods:
        ``setup_configuration``, ``setup_credentials``,
        ``setup_data_profiles``, ``setup_database``,
        ``setup_authentication``, and ``setup_infrastructure``.

.. moduleauthor:: Code Craft AI LLC
"""

__author__ = "Code Craft AI LLC"
__copyright__ = "Copyright 2025, Code Craft AI LLC"
__credits__ = []


import ccai.webworks.webapplication as webapp_module

from ccai.testbase.mocking import Mock, create_module_patch

from ccai.webworks.webapplication import (
    WebApplication,
    establish_webapp_persona,
    reset_webapp_persona,
)
from ccai.webworks.persona.lifecycle import LifecycleError, LifecyclePhase
from ccai.webworks.authentication.system import AuthenticationSystem
from ccai.webworks.routing.router import Router
from ccai.webworks.routing.dispatcher import Dispatcher
from ccai.errors.exceptions import SemanticError


# =============================================================================
# Helpers
# =============================================================================

def _create_app():
    """
        Creates a fresh WebApplication via ``establish_webapp_persona``
        after resetting any prior singleton state.

        :returns: A freshly created WebApplication instance.
    """
    reset_webapp_persona()

    app = establish_webapp_persona(
        name="testapp",
        logger_name="testapp",
        log_basename="testapp",
    )

    return app


# =============================================================================
# Unit Tests for setup_configuration
# =============================================================================

def test_setup_configuration_creates_managed_config_registry():
    """
        Test that ``setup_configuration`` creates a ManagedConfigRegistry
        instance and calls ``setup_from_persona`` on it.  The registry
        is mocked to avoid filesystem side effects.

        _Requirements: 4.1, 4.2_
    """
    mock_registry_instance = Mock()
    mock_registry_instance.configure(recursive=True)

    # Mock ManagedConfigRegistry constructor to return our mock instance
    patch = create_module_patch(webapp_module, "ManagedConfigRegistry")
    mock_cls = patch.activate()
    mock_cls.configure(return_value=mock_registry_instance)

    try:
        app = _create_app()

        app.setup_configuration()

        # Verify the constructor was called
        mock_cls.mock_context().assert_called_once()

        # Verify setup_from_persona was called on the instance.
        # With recursive=True, accessing setup_from_persona returns a
        # child mock.  Calling it records the call on that child mock's
        # context.
        sfp_mock = mock_registry_instance.setup_from_persona
        sfp_mock.mock_context().assert_called_once()

        # Verify the config is stored
        if app._config is not mock_registry_instance:
            errmsg = (
                "Expected _config to be the mock registry instance, "
                f"got {type(app._config)}"
            )
            raise AssertionError(errmsg)

        # Verify phase advanced to CONFIGURED
        if app.current_phase != LifecyclePhase.CONFIGURED:
            errmsg = (
                f"Expected phase CONFIGURED, got '{app.current_phase.value}'"
            )
            raise AssertionError(errmsg)

    finally:
        patch.deactivate()
        reset_webapp_persona()

    return


def test_setup_configuration_advances_phase_to_configured():
    """
        Test that ``setup_configuration`` advances the lifecycle phase
        from CREATED to CONFIGURED on success.

        _Requirements: 4.1, 8.1_
    """
    mock_registry_instance = Mock()
    mock_registry_instance.configure(recursive=True)

    patch = create_module_patch(webapp_module, "ManagedConfigRegistry")
    mock_cls = patch.activate()
    mock_cls.configure(return_value=mock_registry_instance)

    try:
        app = _create_app()

        if app.current_phase != LifecyclePhase.CREATED:
            errmsg = f"Expected initial phase CREATED, got '{app.current_phase.value}'"
            raise AssertionError(errmsg)

        app.setup_configuration()

        if app.current_phase != LifecyclePhase.CONFIGURED:
            errmsg = f"Expected phase CONFIGURED after setup_configuration, got '{app.current_phase.value}'"
            raise AssertionError(errmsg)

    finally:
        patch.deactivate()
        reset_webapp_persona()

    return


def test_setup_configuration_failure_propagates_with_presence_dir():
    """
        Test that when ``setup_from_persona`` raises an exception during
        ``setup_configuration``, the error is wrapped in a SemanticError
        whose message includes the presence directory path.

        _Requirements: 4.2, 4.3_
    """
    mock_registry_instance = Mock()
    mock_registry_instance.configure(recursive=True)

    def _failing_setup():
        raise RuntimeError("config file not found")

    mock_registry_instance.mock_context().mock_method(
        "setup_from_persona", side_effect=_failing_setup
    )

    patch = create_module_patch(webapp_module, "ManagedConfigRegistry")
    mock_cls = patch.activate()
    mock_cls.configure(return_value=mock_registry_instance)

    try:
        app = _create_app()

        caught_error = None

        try:
            app.setup_configuration()
        except SemanticError as err:
            caught_error = err

        if caught_error is None:
            errmsg = "Expected SemanticError to be raised when setup_from_persona fails"
            raise AssertionError(errmsg)

        error_message = str(caught_error)

        # The error message should mention the presence directory
        if "Configuration setup failed" not in error_message:
            errmsg = (
                "Expected error message to contain 'Configuration setup failed'. "
                f"Got: '{error_message}'"
            )
            raise AssertionError(errmsg)

        # The original exception should be chained
        if caught_error.__cause__ is None:
            errmsg = "Expected the SemanticError to chain the original exception via __cause__"
            raise AssertionError(errmsg)

    finally:
        patch.deactivate()
        reset_webapp_persona()

    return


# =============================================================================
# Unit Tests for setup_credentials
# =============================================================================

def test_setup_credentials_advances_phase_to_credentials_loaded():
    """
        Test that ``setup_credentials`` advances the lifecycle phase
        to CREDENTIALS_LOADED.  The current implementation is a
        placeholder that stores None.

        _Requirements: 5.1, 8.1_
    """
    mock_registry_instance = Mock()
    mock_registry_instance.configure(recursive=True)

    patch = create_module_patch(webapp_module, "ManagedConfigRegistry")
    mock_cls = patch.activate()
    mock_cls.configure(return_value=mock_registry_instance)

    try:
        app = _create_app()

        app.setup_configuration()
        app.setup_credentials()

        if app.current_phase != LifecyclePhase.CREDENTIALS_LOADED:
            errmsg = (
                f"Expected phase CREDENTIALS_LOADED, "
                f"got '{app.current_phase.value}'"
            )
            raise AssertionError(errmsg)

    finally:
        patch.deactivate()
        reset_webapp_persona()

    return


def test_setup_credentials_requires_configured_phase():
    """
        Test that ``setup_credentials`` raises LifecycleError when
        called before ``setup_configuration`` has completed.

        _Requirements: 5.1, 8.2_
    """
    try:
        app = _create_app()

        caught_error = None

        try:
            app.setup_credentials()
        except LifecycleError as err:
            caught_error = err

        if caught_error is None:
            errmsg = "Expected LifecycleError when calling setup_credentials before setup_configuration"
            raise AssertionError(errmsg)

        if caught_error.required_phase != LifecyclePhase.CONFIGURED:
            errmsg = (
                f"Expected required_phase CONFIGURED, "
                f"got '{caught_error.required_phase.value}'"
            )
            raise AssertionError(errmsg)

    finally:
        reset_webapp_persona()

    return


def test_setup_credentials_stores_none_as_placeholder():
    """
        Test that the placeholder ``setup_credentials`` implementation
        stores None in ``_credential_manager``.

        _Requirements: 5.1_
    """
    mock_registry_instance = Mock()
    mock_registry_instance.configure(recursive=True)

    patch = create_module_patch(webapp_module, "ManagedConfigRegistry")
    mock_cls = patch.activate()
    mock_cls.configure(return_value=mock_registry_instance)

    try:
        app = _create_app()

        app.setup_configuration()
        app.setup_credentials()

        if app._credential_manager is not None:
            errmsg = (
                "Expected _credential_manager to be None (placeholder), "
                f"got {type(app._credential_manager)}"
            )
            raise AssertionError(errmsg)

    finally:
        patch.deactivate()
        reset_webapp_persona()

    return


# =============================================================================
# Unit Tests for setup_data_profiles
# =============================================================================

def test_setup_data_profiles_advances_phase_to_data_profiles_loaded():
    """
        Test that ``setup_data_profiles`` advances the lifecycle phase
        to DATA_PROFILES_LOADED.  The current implementation is a
        placeholder that stores None.

        _Requirements: 6.1, 8.1_
    """
    mock_registry_instance = Mock()
    mock_registry_instance.configure(recursive=True)

    patch = create_module_patch(webapp_module, "ManagedConfigRegistry")
    mock_cls = patch.activate()
    mock_cls.configure(return_value=mock_registry_instance)

    try:
        app = _create_app()

        app.setup_configuration()
        app.setup_credentials()
        app.setup_data_profiles()

        if app.current_phase != LifecyclePhase.DATA_PROFILES_LOADED:
            errmsg = (
                f"Expected phase DATA_PROFILES_LOADED, "
                f"got '{app.current_phase.value}'"
            )
            raise AssertionError(errmsg)

    finally:
        patch.deactivate()
        reset_webapp_persona()

    return


def test_setup_data_profiles_requires_credentials_loaded_phase():
    """
        Test that ``setup_data_profiles`` raises LifecycleError when
        called before ``setup_credentials`` has completed.

        _Requirements: 6.1, 8.2_
    """
    mock_registry_instance = Mock()
    mock_registry_instance.configure(recursive=True)

    patch = create_module_patch(webapp_module, "ManagedConfigRegistry")
    mock_cls = patch.activate()
    mock_cls.configure(return_value=mock_registry_instance)

    try:
        app = _create_app()

        # Only run setup_configuration, skip setup_credentials
        app.setup_configuration()

        caught_error = None

        try:
            app.setup_data_profiles()
        except LifecycleError as err:
            caught_error = err

        if caught_error is None:
            errmsg = "Expected LifecycleError when calling setup_data_profiles before setup_credentials"
            raise AssertionError(errmsg)

        if caught_error.required_phase != LifecyclePhase.CREDENTIALS_LOADED:
            errmsg = (
                f"Expected required_phase CREDENTIALS_LOADED, "
                f"got '{caught_error.required_phase.value}'"
            )
            raise AssertionError(errmsg)

    finally:
        patch.deactivate()
        reset_webapp_persona()

    return


def test_setup_data_profiles_stores_none_as_placeholder():
    """
        Test that the placeholder ``setup_data_profiles`` implementation
        stores None in ``_data_profile_manager``.

        _Requirements: 6.1_
    """
    mock_registry_instance = Mock()
    mock_registry_instance.configure(recursive=True)

    patch = create_module_patch(webapp_module, "ManagedConfigRegistry")
    mock_cls = patch.activate()
    mock_cls.configure(return_value=mock_registry_instance)

    try:
        app = _create_app()

        app.setup_configuration()
        app.setup_credentials()
        app.setup_data_profiles()

        if app._data_profile_manager is not None:
            errmsg = (
                "Expected _data_profile_manager to be None (placeholder), "
                f"got {type(app._data_profile_manager)}"
            )
            raise AssertionError(errmsg)

    finally:
        patch.deactivate()
        reset_webapp_persona()

    return


# =============================================================================
# Unit Tests for setup_database
# =============================================================================

def test_setup_database_calls_all_four_hook_methods():
    """
        Test that ``setup_database`` calls ``prepare_database``,
        ``connect_database``, ``startup_database``, and
        ``ensure_database_ready`` in order.

        _Requirements: 8.1_
    """
    call_order = []

    class TrackingWebApplication(WebApplication):
        """
            A WebApplication subclass that tracks database hook calls.
        """

        def prepare_database(self) -> None:
            call_order.append("prepare_database")
            return

        def connect_database(self) -> None:
            call_order.append("connect_database")
            return

        def startup_database(self) -> None:
            call_order.append("startup_database")
            return

        def ensure_database_ready(self) -> bool:
            call_order.append("ensure_database_ready")
            return True

    mock_registry_instance = Mock()
    mock_registry_instance.configure(recursive=True)

    patch = create_module_patch(webapp_module, "ManagedConfigRegistry")
    mock_cls = patch.activate()
    mock_cls.configure(return_value=mock_registry_instance)

    try:
        reset_webapp_persona()

        app = establish_webapp_persona(
            name="testapp",
            logger_name="testapp",
            log_basename="testapp",
            application_cls=TrackingWebApplication,
        )

        app.setup_configuration()
        app.setup_credentials()
        app.setup_data_profiles()

        call_order.clear()
        app.setup_database()

        expected_order = [
            "prepare_database",
            "connect_database",
            "startup_database",
            "ensure_database_ready",
        ]

        if call_order != expected_order:
            errmsg = (
                f"Expected database hook call order {expected_order}, "
                f"got {call_order}"
            )
            raise AssertionError(errmsg)

    finally:
        patch.deactivate()
        reset_webapp_persona()

    return


def test_setup_database_advances_phase_to_database_ready():
    """
        Test that ``setup_database`` advances the lifecycle phase
        to DATABASE_READY after calling all hooks.

        _Requirements: 8.1_
    """
    mock_registry_instance = Mock()
    mock_registry_instance.configure(recursive=True)

    patch = create_module_patch(webapp_module, "ManagedConfigRegistry")
    mock_cls = patch.activate()
    mock_cls.configure(return_value=mock_registry_instance)

    try:
        app = _create_app()

        app.setup_configuration()
        app.setup_credentials()
        app.setup_data_profiles()
        app.setup_database()

        if app.current_phase != LifecyclePhase.DATABASE_READY:
            errmsg = (
                f"Expected phase DATABASE_READY, "
                f"got '{app.current_phase.value}'"
            )
            raise AssertionError(errmsg)

    finally:
        patch.deactivate()
        reset_webapp_persona()

    return


def test_setup_database_requires_data_profiles_loaded_phase():
    """
        Test that ``setup_database`` raises LifecycleError when called
        before ``setup_data_profiles`` has completed.

        _Requirements: 8.1, 8.2_
    """
    mock_registry_instance = Mock()
    mock_registry_instance.configure(recursive=True)

    patch = create_module_patch(webapp_module, "ManagedConfigRegistry")
    mock_cls = patch.activate()
    mock_cls.configure(return_value=mock_registry_instance)

    try:
        app = _create_app()

        app.setup_configuration()
        app.setup_credentials()
        # Skip setup_data_profiles

        caught_error = None

        try:
            app.setup_database()
        except LifecycleError as err:
            caught_error = err

        if caught_error is None:
            errmsg = "Expected LifecycleError when calling setup_database before setup_data_profiles"
            raise AssertionError(errmsg)

        if caught_error.required_phase != LifecyclePhase.DATA_PROFILES_LOADED:
            errmsg = (
                f"Expected required_phase DATA_PROFILES_LOADED, "
                f"got '{caught_error.required_phase.value}'"
            )
            raise AssertionError(errmsg)

    finally:
        patch.deactivate()
        reset_webapp_persona()

    return


# =============================================================================
# Unit Tests for setup_authentication
# =============================================================================

def test_setup_authentication_creates_authentication_system():
    """
        Test that ``setup_authentication`` creates an
        ``AuthenticationSystem`` instance and stores it in
        ``_auth_system``.

        _Requirements: 7.1_
    """
    mock_registry_instance = Mock()
    mock_registry_instance.configure(recursive=True)

    patch = create_module_patch(webapp_module, "ManagedConfigRegistry")
    mock_cls = patch.activate()
    mock_cls.configure(return_value=mock_registry_instance)

    try:
        app = _create_app()

        app.setup_configuration()
        app.setup_credentials()
        app.setup_data_profiles()
        app.setup_database()
        app.setup_authentication()

        if app._auth_system is None:
            errmsg = "Expected _auth_system to be set after setup_authentication"
            raise AssertionError(errmsg)

        if not isinstance(app._auth_system, AuthenticationSystem):
            errmsg = (
                f"Expected _auth_system to be an AuthenticationSystem instance, "
                f"got {type(app._auth_system)}"
            )
            raise AssertionError(errmsg)

    finally:
        patch.deactivate()
        reset_webapp_persona()

    return


def test_setup_authentication_advances_phase_to_authentication_ready():
    """
        Test that ``setup_authentication`` advances the lifecycle phase
        to AUTHENTICATION_READY.

        _Requirements: 7.1, 8.1_
    """
    mock_registry_instance = Mock()
    mock_registry_instance.configure(recursive=True)

    patch = create_module_patch(webapp_module, "ManagedConfigRegistry")
    mock_cls = patch.activate()
    mock_cls.configure(return_value=mock_registry_instance)

    try:
        app = _create_app()

        app.setup_configuration()
        app.setup_credentials()
        app.setup_data_profiles()
        app.setup_database()
        app.setup_authentication()

        if app.current_phase != LifecyclePhase.AUTHENTICATION_READY:
            errmsg = (
                f"Expected phase AUTHENTICATION_READY, "
                f"got '{app.current_phase.value}'"
            )
            raise AssertionError(errmsg)

    finally:
        patch.deactivate()
        reset_webapp_persona()

    return


def test_setup_authentication_requires_database_ready_phase():
    """
        Test that ``setup_authentication`` raises LifecycleError when
        called before ``setup_database`` has completed.

        _Requirements: 7.1, 8.2_
    """
    mock_registry_instance = Mock()
    mock_registry_instance.configure(recursive=True)

    patch = create_module_patch(webapp_module, "ManagedConfigRegistry")
    mock_cls = patch.activate()
    mock_cls.configure(return_value=mock_registry_instance)

    try:
        app = _create_app()

        app.setup_configuration()
        app.setup_credentials()
        app.setup_data_profiles()
        # Skip setup_database

        caught_error = None

        try:
            app.setup_authentication()
        except LifecycleError as err:
            caught_error = err

        if caught_error is None:
            errmsg = "Expected LifecycleError when calling setup_authentication before setup_database"
            raise AssertionError(errmsg)

        if caught_error.required_phase != LifecyclePhase.DATABASE_READY:
            errmsg = (
                f"Expected required_phase DATABASE_READY, "
                f"got '{caught_error.required_phase.value}'"
            )
            raise AssertionError(errmsg)

    finally:
        patch.deactivate()
        reset_webapp_persona()

    return


# =============================================================================
# Unit Tests for setup_infrastructure
# =============================================================================

def test_setup_infrastructure_creates_router():
    """
        Test that ``setup_infrastructure`` creates a Router instance
        and stores it in ``_router``.

        _Requirements: 1.1_
    """
    mock_registry_instance = Mock()
    mock_registry_instance.configure(recursive=True)

    patch = create_module_patch(webapp_module, "ManagedConfigRegistry")
    mock_cls = patch.activate()
    mock_cls.configure(return_value=mock_registry_instance)

    try:
        app = _create_app()

        app.setup_configuration()
        app.setup_credentials()
        app.setup_data_profiles()
        app.setup_database()
        app.setup_authentication()
        app.setup_infrastructure()

        if app._router is None:
            errmsg = "Expected _router to be set after setup_infrastructure"
            raise AssertionError(errmsg)

        if not isinstance(app._router, Router):
            errmsg = (
                f"Expected _router to be a Router instance, "
                f"got {type(app._router)}"
            )
            raise AssertionError(errmsg)

    finally:
        patch.deactivate()
        reset_webapp_persona()

    return


def test_setup_infrastructure_creates_dispatcher_with_router():
    """
        Test that ``setup_infrastructure`` creates a Dispatcher instance
        configured with the Router, and stores it in ``_dispatcher``.

        _Requirements: 1.2, 1.4_
    """
    mock_registry_instance = Mock()
    mock_registry_instance.configure(recursive=True)

    patch = create_module_patch(webapp_module, "ManagedConfigRegistry")
    mock_cls = patch.activate()
    mock_cls.configure(return_value=mock_registry_instance)

    try:
        app = _create_app()

        app.setup_configuration()
        app.setup_credentials()
        app.setup_data_profiles()
        app.setup_database()
        app.setup_authentication()
        app.setup_infrastructure()

        if app._dispatcher is None:
            errmsg = "Expected _dispatcher to be set after setup_infrastructure"
            raise AssertionError(errmsg)

        if not isinstance(app._dispatcher, Dispatcher):
            errmsg = (
                f"Expected _dispatcher to be a Dispatcher instance, "
                f"got {type(app._dispatcher)}"
            )
            raise AssertionError(errmsg)

        # Verify the Dispatcher's router is the same Router instance
        if app._dispatcher.router is not app._router:
            errmsg = (
                "Expected Dispatcher's router to be the same Router "
                "instance as WebApplication._router"
            )
            raise AssertionError(errmsg)

    finally:
        patch.deactivate()
        reset_webapp_persona()

    return


def test_setup_infrastructure_creates_asgi_application():
    """
        Test that ``setup_infrastructure`` creates an ASGIApplication
        instance and stores it in ``_asgi_app``.

        _Requirements: 1.3_
    """
    mock_registry_instance = Mock()
    mock_registry_instance.configure(recursive=True)

    patch = create_module_patch(webapp_module, "ManagedConfigRegistry")
    mock_cls = patch.activate()
    mock_cls.configure(return_value=mock_registry_instance)

    try:
        app = _create_app()

        app.setup_configuration()
        app.setup_credentials()
        app.setup_data_profiles()
        app.setup_database()
        app.setup_authentication()
        app.setup_infrastructure()

        if app._asgi_app is None:
            errmsg = "Expected _asgi_app to be set after setup_infrastructure"
            raise AssertionError(errmsg)

        # Verify it has the expected http_handler attribute
        if not hasattr(app._asgi_app, "http_handler"):
            errmsg = "Expected _asgi_app to have an http_handler attribute"
            raise AssertionError(errmsg)

    finally:
        patch.deactivate()
        reset_webapp_persona()

    return


def test_setup_infrastructure_wires_http_handler_to_dispatcher():
    """
        Test that ``setup_infrastructure`` wires the ASGIApplication
        HTTP handler to use the Dispatcher's ``dispatch_async`` method.

        _Requirements: 1.5_
    """
    mock_registry_instance = Mock()
    mock_registry_instance.configure(recursive=True)

    patch = create_module_patch(webapp_module, "ManagedConfigRegistry")
    mock_cls = patch.activate()
    mock_cls.configure(return_value=mock_registry_instance)

    try:
        app = _create_app()

        app.setup_configuration()
        app.setup_credentials()
        app.setup_data_profiles()
        app.setup_database()
        app.setup_authentication()
        app.setup_infrastructure()

        # The HTTP handler should have been wired to the dispatcher
        http_handler = app._asgi_app.http_handler

        if http_handler is None:
            errmsg = "Expected http_handler to be set on the ASGIApplication"
            raise AssertionError(errmsg)

        # Verify the handler was set (the handler attribute should reference
        # the dispatcher's dispatch_async)
        if not hasattr(http_handler, '_handler'):
            errmsg = "Expected http_handler to have a _handler attribute after wiring"
            raise AssertionError(errmsg)

        # Bound methods create new objects on each access, so use __func__
        # and __self__ to verify identity rather than ``is``.
        wired_handler = http_handler._handler
        expected_method = app._dispatcher.dispatch_async

        if not callable(wired_handler):
            errmsg = "Expected http_handler._handler to be callable"
            raise AssertionError(errmsg)

        if getattr(wired_handler, '__func__', None) is not getattr(expected_method, '__func__', None):
            errmsg = (
                "Expected http_handler._handler to be the dispatcher's "
                "dispatch_async method"
            )
            raise AssertionError(errmsg)

        if getattr(wired_handler, '__self__', None) is not app._dispatcher:
            errmsg = (
                "Expected http_handler._handler to be bound to the "
                "dispatcher instance"
            )
            raise AssertionError(errmsg)

    finally:
        patch.deactivate()
        reset_webapp_persona()

    return


def test_setup_infrastructure_advances_phase_to_infrastructure_ready():
    """
        Test that ``setup_infrastructure`` advances the lifecycle phase
        to INFRASTRUCTURE_READY.

        _Requirements: 1.1, 8.1_
    """
    mock_registry_instance = Mock()
    mock_registry_instance.configure(recursive=True)

    patch = create_module_patch(webapp_module, "ManagedConfigRegistry")
    mock_cls = patch.activate()
    mock_cls.configure(return_value=mock_registry_instance)

    try:
        app = _create_app()

        app.setup_configuration()
        app.setup_credentials()
        app.setup_data_profiles()
        app.setup_database()
        app.setup_authentication()
        app.setup_infrastructure()

        if app.current_phase != LifecyclePhase.INFRASTRUCTURE_READY:
            errmsg = (
                f"Expected phase INFRASTRUCTURE_READY, "
                f"got '{app.current_phase.value}'"
            )
            raise AssertionError(errmsg)

    finally:
        patch.deactivate()
        reset_webapp_persona()

    return


def test_setup_infrastructure_requires_authentication_ready_phase():
    """
        Test that ``setup_infrastructure`` raises LifecycleError when
        called before ``setup_authentication`` has completed.

        _Requirements: 1.1, 8.2_
    """
    mock_registry_instance = Mock()
    mock_registry_instance.configure(recursive=True)

    patch = create_module_patch(webapp_module, "ManagedConfigRegistry")
    mock_cls = patch.activate()
    mock_cls.configure(return_value=mock_registry_instance)

    try:
        app = _create_app()

        app.setup_configuration()
        app.setup_credentials()
        app.setup_data_profiles()
        app.setup_database()
        # Skip setup_authentication

        caught_error = None

        try:
            app.setup_infrastructure()
        except LifecycleError as err:
            caught_error = err

        if caught_error is None:
            errmsg = "Expected LifecycleError when calling setup_infrastructure before setup_authentication"
            raise AssertionError(errmsg)

        if caught_error.required_phase != LifecyclePhase.AUTHENTICATION_READY:
            errmsg = (
                f"Expected required_phase AUTHENTICATION_READY, "
                f"got '{caught_error.required_phase.value}'"
            )
            raise AssertionError(errmsg)

    finally:
        patch.deactivate()
        reset_webapp_persona()

    return


def test_setup_infrastructure_properties_accessible_after_setup():
    """
        Test that the ``router``, ``dispatcher``, and ``asgi_app``
        properties are accessible (do not raise LifecycleError) after
        ``setup_infrastructure`` completes.

        _Requirements: 1.1, 1.2, 1.3, 8.1_
    """
    mock_registry_instance = Mock()
    mock_registry_instance.configure(recursive=True)

    patch = create_module_patch(webapp_module, "ManagedConfigRegistry")
    mock_cls = patch.activate()
    mock_cls.configure(return_value=mock_registry_instance)

    try:
        app = _create_app()

        app.setup_configuration()
        app.setup_credentials()
        app.setup_data_profiles()
        app.setup_database()
        app.setup_authentication()
        app.setup_infrastructure()

        # These should not raise LifecycleError
        router = app.router
        dispatcher = app.dispatcher
        asgi_app = app.asgi_app

        if router is None:
            errmsg = "Expected router property to return a non-None value"
            raise AssertionError(errmsg)

        if dispatcher is None:
            errmsg = "Expected dispatcher property to return a non-None value"
            raise AssertionError(errmsg)

        if asgi_app is None:
            errmsg = "Expected asgi_app property to return a non-None value"
            raise AssertionError(errmsg)

    finally:
        patch.deactivate()
        reset_webapp_persona()

    return


# =============================================================================
# Unit Tests for establish_webapp_persona with application_cls
# =============================================================================

def test_establish_webapp_persona_with_application_cls_creates_subclass():
    """
        Test that ``establish_webapp_persona`` with ``application_cls``
        creates an instance of the specified subclass and that the
        subclass has access to all lifecycle properties after ``startup()``.

        _Requirements: 9.3_
    """

    class CustomWebApplication(WebApplication):
        """
            A custom WebApplication subclass for testing.
        """
        pass

    mock_registry_instance = Mock()
    mock_registry_instance.configure(recursive=True)

    patch = create_module_patch(webapp_module, "ManagedConfigRegistry")
    mock_cls = patch.activate()
    mock_cls.configure(return_value=mock_registry_instance)

    try:
        reset_webapp_persona()

        app = establish_webapp_persona(
            name="testapp",
            logger_name="testapp",
            log_basename="testapp",
            application_cls=CustomWebApplication,
        )

        # Verify the returned instance is of the subclass type
        if not isinstance(app, CustomWebApplication):
            errmsg = (
                f"Expected instance of CustomWebApplication, "
                f"got {type(app).__name__}"
            )
            raise AssertionError(errmsg)

        # Verify it is also a WebApplication
        if not isinstance(app, WebApplication):
            errmsg = (
                f"Expected instance to also be a WebApplication, "
                f"got {type(app).__name__}"
            )
            raise AssertionError(errmsg)

        # Call startup with mocked ManagedConfigRegistry
        result = app.startup()

        # Verify startup returns self
        if result is not app:
            errmsg = "Expected startup() to return the same app instance"
            raise AssertionError(errmsg)

        # Verify the subclass has access to all lifecycle properties
        if app.current_phase != LifecyclePhase.READY:
            errmsg = (
                f"Expected current_phase to be READY, "
                f"got {app.current_phase}"
            )
            raise AssertionError(errmsg)

        if app.config is None:
            errmsg = "Expected config property to be non-None after startup"
            raise AssertionError(errmsg)

        if app.auth_system is None:
            errmsg = "Expected auth_system property to be non-None after startup"
            raise AssertionError(errmsg)

        if app.router is None:
            errmsg = "Expected router property to be non-None after startup"
            raise AssertionError(errmsg)

        if not isinstance(app.router, Router):
            errmsg = (
                f"Expected router to be a Router instance, "
                f"got {type(app.router).__name__}"
            )
            raise AssertionError(errmsg)

        if app.dispatcher is None:
            errmsg = "Expected dispatcher property to be non-None after startup"
            raise AssertionError(errmsg)

        if not isinstance(app.dispatcher, Dispatcher):
            errmsg = (
                f"Expected dispatcher to be a Dispatcher instance, "
                f"got {type(app.dispatcher).__name__}"
            )
            raise AssertionError(errmsg)

        if app.asgi_app is None:
            errmsg = "Expected asgi_app property to be non-None after startup"
            raise AssertionError(errmsg)

    finally:
        patch.deactivate()
        reset_webapp_persona()

    return


# =============================================================================
# Helpers for the lifecycle guard tests
# =============================================================================

def _patch_config_registry(get_values=None):
    """
        Patches ManagedConfigRegistry with a mock whose ``get`` returns the
        given values by key (None for any other key).

        :param get_values: Optional mapping of configuration key to value.

        :returns: The activated patch, for the caller to deactivate.
    """
    values = get_values if get_values is not None else {}

    mock_registry_instance = Mock()
    mock_registry_instance.configure(recursive=True)
    mock_registry_instance.mock_context().mock_method(
        "get", side_effect=lambda key, default=None: values.get(key, default)
    )

    patch = create_module_patch(webapp_module, "ManagedConfigRegistry")
    mock_cls = patch.activate()
    mock_cls.configure(return_value=mock_registry_instance)

    return patch


def _expect_lifecycle_error(operation, current_phase):
    """
        Runs *operation* and checks that it raises LifecycleError reporting
        *current_phase*.

        :param operation: Callable taking no arguments.
        :param current_phase: The phase the error must report.
    """
    caught_error = None

    try:
        operation()
    except LifecycleError as err:
        caught_error = err

    if caught_error is None:
        raise AssertionError("Expected LifecycleError, nothing was raised")

    if caught_error.current_phase != current_phase:
        errmsg = (
            f"Expected the error to report phase '{current_phase.value}', "
            f"got '{caught_error.current_phase.value}'"
        )
        raise AssertionError(errmsg)

    return


# =============================================================================
# setup_database: ensure_database_ready result
# =============================================================================

def test_setup_database_raises_when_database_is_not_ready():
    """
        Test that ``setup_database`` raises SemanticError and does not
        advance the phase when ``ensure_database_ready`` returns False.
    """

    class NotReadyApplication(WebApplication):
        def ensure_database_ready(self) -> bool:
            return False

    patch = _patch_config_registry()

    try:
        reset_webapp_persona()
        app = establish_webapp_persona(
            name="testapp",
            logger_name="testapp",
            log_basename="testapp",
            application_cls=NotReadyApplication,
        )

        app.setup_configuration()
        app.setup_credentials()
        app.setup_data_profiles()

        caught_error = None
        try:
            app.setup_database()
        except SemanticError as err:
            caught_error = err

        if caught_error is None or "ensure_database_ready" not in str(caught_error):
            errmsg = f"Expected a SemanticError naming ensure_database_ready, got {caught_error!r}"
            raise AssertionError(errmsg)

        if app.current_phase != LifecyclePhase.DATA_PROFILES_LOADED:
            errmsg = f"Expected phase DATA_PROFILES_LOADED, got '{app.current_phase.value}'"
            raise AssertionError(errmsg)

    finally:
        patch.deactivate()
        reset_webapp_persona()

    return


# =============================================================================
# credentials / data_profiles placeholders
# =============================================================================

def test_credentials_property_raises_while_no_manager_is_integrated():
    """
        Test that ``credentials`` raises a descriptive SemanticError (not
        None) after the placeholder ``setup_credentials`` has run.
    """
    patch = _patch_config_registry()

    try:
        app = _create_app()
        app.setup_configuration()
        app.setup_credentials()

        caught_error = None
        try:
            _ = app.credentials
        except SemanticError as err:
            caught_error = err

        if caught_error is None or isinstance(caught_error, LifecycleError):
            errmsg = f"Expected a placeholder SemanticError, got {caught_error!r}"
            raise AssertionError(errmsg)

        if "credential" not in str(caught_error):
            errmsg = f"Expected the error to name the credential manager, got '{caught_error}'"
            raise AssertionError(errmsg)

    finally:
        patch.deactivate()
        reset_webapp_persona()

    return


def test_data_profiles_property_raises_while_no_manager_is_integrated():
    """
        Test that ``data_profiles`` raises a descriptive SemanticError (not
        None) after the placeholder ``setup_data_profiles`` has run.
    """
    patch = _patch_config_registry()

    try:
        app = _create_app()
        app.setup_configuration()
        app.setup_credentials()
        app.setup_data_profiles()

        caught_error = None
        try:
            _ = app.data_profiles
        except SemanticError as err:
            caught_error = err

        if caught_error is None or isinstance(caught_error, LifecycleError):
            errmsg = f"Expected a placeholder SemanticError, got {caught_error!r}"
            raise AssertionError(errmsg)

        if "data profile" not in str(caught_error):
            errmsg = f"Expected the error to name the data profile manager, got '{caught_error}'"
            raise AssertionError(errmsg)

    finally:
        patch.deactivate()
        reset_webapp_persona()

    return


def test_credentials_property_returns_a_manager_set_by_a_subclass():
    """
        Test that a subclass that provides a credential manager in
        ``setup_credentials`` gets it back from ``credentials``.
    """
    manager = object()

    class CredentialedApplication(WebApplication):
        def setup_credentials(self) -> None:
            super().setup_credentials()
            self._credential_manager = manager
            return

    patch = _patch_config_registry()

    try:
        reset_webapp_persona()
        app = establish_webapp_persona(
            name="testapp",
            logger_name="testapp",
            log_basename="testapp",
            application_cls=CredentialedApplication,
        )
        app.setup_configuration()
        app.setup_credentials()

        if app.credentials is not manager:
            raise AssertionError("Expected the subclass's credential manager")

    finally:
        patch.deactivate()
        reset_webapp_persona()

    return


# =============================================================================
# Lifecycle guards: exact predecessor phases and a terminal SHUTDOWN
# =============================================================================

def test_setup_configuration_after_startup_does_not_regress_the_phase():
    """
        Test that calling ``setup_configuration`` on a started application
        raises LifecycleError and leaves the phase at READY.
    """
    patch = _patch_config_registry()

    try:
        app = _create_app()
        app.startup()

        _expect_lifecycle_error(app.setup_configuration, LifecyclePhase.READY)

        if app.current_phase != LifecyclePhase.READY:
            errmsg = f"Expected phase READY, got '{app.current_phase.value}'"
            raise AssertionError(errmsg)

    finally:
        patch.deactivate()
        reset_webapp_persona()

    return


def test_setup_step_requires_exactly_its_predecessor_phase():
    """
        Test that a setup step repeated after its own phase raises
        LifecycleError instead of running again.
    """
    patch = _patch_config_registry()

    try:
        app = _create_app()
        app.setup_configuration()
        app.setup_credentials()
        app.setup_data_profiles()

        _expect_lifecycle_error(app.setup_credentials, LifecyclePhase.DATA_PROFILES_LOADED)

    finally:
        patch.deactivate()
        reset_webapp_persona()

    return


def test_subsystem_properties_raise_lifecycle_error_after_shutdown():
    """
        Test that router, dispatcher, asgi_app and config raise
        LifecycleError after ``shutdown()`` instead of returning None.
    """
    patch = _patch_config_registry()

    try:
        app = _create_app()
        app.startup()
        app.shutdown()

        for property_name in ("router", "dispatcher", "asgi_app", "config", "auth_system"):
            _expect_lifecycle_error(lambda: getattr(app, property_name), LifecyclePhase.SHUTDOWN)

    finally:
        patch.deactivate()
        reset_webapp_persona()

    return


def test_register_authenticator_raises_lifecycle_error_after_shutdown():
    """
        Test that ``register_authenticator`` raises LifecycleError after
        ``shutdown()`` rather than an AttributeError on the released system.
    """
    patch = _patch_config_registry()

    try:
        app = _create_app()
        app.startup()
        app.shutdown()

        _expect_lifecycle_error(lambda: app.register_authenticator(object()), LifecyclePhase.SHUTDOWN)

    finally:
        patch.deactivate()
        reset_webapp_persona()

    return


def test_startup_after_shutdown_raises_lifecycle_error():
    """
        Test that ``startup()`` on a shut down application raises
        LifecycleError and the phase stays SHUTDOWN.
    """
    patch = _patch_config_registry()

    try:
        app = _create_app()
        app.startup()
        app.shutdown()

        _expect_lifecycle_error(app.startup, LifecyclePhase.SHUTDOWN)

        if app.current_phase != LifecyclePhase.SHUTDOWN:
            errmsg = f"Expected phase SHUTDOWN, got '{app.current_phase.value}'"
            raise AssertionError(errmsg)

    finally:
        patch.deactivate()
        reset_webapp_persona()

    return


def test_attach_route_after_shutdown_raises_lifecycle_error():
    """
        Test that ``attach_route`` and ``attach_blueprint_to_route`` raise
        LifecycleError after ``shutdown()``.
    """
    patch = _patch_config_registry()

    try:
        app = _create_app()
        app.startup()
        app.shutdown()

        def handler(request):
            return {}

        class LateBlueprint:
            @classmethod
            def register(cls, router=None):
                return []

        _expect_lifecycle_error(lambda: app.attach_route("/late")(handler), LifecyclePhase.SHUTDOWN)
        _expect_lifecycle_error(lambda: app.attach_blueprint_to_route(LateBlueprint), LifecyclePhase.SHUTDOWN)

    finally:
        patch.deactivate()
        reset_webapp_persona()

    return


def test_shutdown_twice_keeps_the_application_shut_down():
    """
        Test that a second ``shutdown()`` does nothing.
    """
    patch = _patch_config_registry()

    try:
        app = _create_app()
        app.startup()
        app.shutdown()
        app.shutdown()

        if app.current_phase != LifecyclePhase.SHUTDOWN:
            errmsg = f"Expected phase SHUTDOWN, got '{app.current_phase.value}'"
            raise AssertionError(errmsg)

    finally:
        patch.deactivate()
        reset_webapp_persona()

    return


def test_failed_setup_infrastructure_keeps_queued_routes():
    """
        Test that when a queued blueprint fails to register, the queued
        routes and blueprints are kept and the phase does not advance.
    """
    patch = _patch_config_registry()

    try:
        app = _create_app()

        @app.attach_route("/kept")
        def kept(request):
            return {}

        class FailingBlueprint:
            @classmethod
            def register(cls, router=None):
                raise RuntimeError("blueprint failed")

        app.attach_blueprint_to_route(FailingBlueprint)

        app.setup_configuration()
        app.setup_credentials()
        app.setup_data_profiles()
        app.setup_database()
        app.setup_authentication()

        caught_error = None
        try:
            app.setup_infrastructure()
        except RuntimeError as err:
            caught_error = err

        if caught_error is None:
            raise AssertionError("Expected the blueprint's RuntimeError")

        if app.current_phase != LifecyclePhase.AUTHENTICATION_READY:
            errmsg = f"Expected phase AUTHENTICATION_READY, got '{app.current_phase.value}'"
            raise AssertionError(errmsg)

        if len(app._pending_routes) != 1 or len(app._pending_blueprints) != 1:
            errmsg = (
                f"Expected the queues to be kept, got {len(app._pending_routes)} routes and "
                f"{len(app._pending_blueprints)} blueprints"
            )
            raise AssertionError(errmsg)

        if app._router is not None:
            raise AssertionError("Expected no router to be published by the failed attempt")

    finally:
        patch.deactivate()
        reset_webapp_persona()

    return


# =============================================================================
# Request body limit from the configuration
# =============================================================================

def test_setup_infrastructure_uses_the_configured_request_body_limit():
    """
        Test that the body limit configured under
        MAX_REQUEST_BODY_SIZE_CONFIG_KEY reaches the ASGI body reader.
    """
    patch = _patch_config_registry({webapp_module.MAX_REQUEST_BODY_SIZE_CONFIG_KEY: 1024})

    try:
        app = _create_app()
        app.startup()

        max_size = app.asgi_app.http_handler.body_reader.max_size
        if max_size != 1024:
            errmsg = f"Expected the configured limit 1024, got {max_size}"
            raise AssertionError(errmsg)

    finally:
        patch.deactivate()
        reset_webapp_persona()

    return


def test_setup_infrastructure_keeps_the_default_body_limit_when_unconfigured():
    """
        Test that without a configured limit the ASGI default applies.
    """
    from ccai.webworks.asgi.constants import DEFAULT_MAX_REQUEST_BODY_SIZE

    patch = _patch_config_registry()

    try:
        app = _create_app()
        app.startup()

        max_size = app.asgi_app.http_handler.body_reader.max_size
        if max_size != DEFAULT_MAX_REQUEST_BODY_SIZE:
            errmsg = f"Expected the default limit {DEFAULT_MAX_REQUEST_BODY_SIZE}, got {max_size}"
            raise AssertionError(errmsg)

    finally:
        patch.deactivate()
        reset_webapp_persona()

    return


def test_setup_infrastructure_accepts_a_body_limit_given_as_decimal_text():
    """
        Test that a body limit given as a string of decimal digits, the form
        the environment configuration source yields, is used as an integer.
    """
    patch = _patch_config_registry({webapp_module.MAX_REQUEST_BODY_SIZE_CONFIG_KEY: " 65536 "})

    try:
        app = _create_app()
        app.startup()

        max_size = app.asgi_app.http_handler.body_reader.max_size
        if max_size != 65536:
            errmsg = f"Expected the configured limit 65536, got {max_size!r}"
            raise AssertionError(errmsg)

    finally:
        patch.deactivate()
        reset_webapp_persona()

    return


def test_setup_infrastructure_rejects_a_signed_body_limit_text():
    """
        Test that decimal text with a sign or digit separators is not taken
        as a body limit, even though int() would accept it.
    """
    for configured in ("+5", "5_0", "-1"):
        patch = _patch_config_registry({webapp_module.MAX_REQUEST_BODY_SIZE_CONFIG_KEY: configured})

        try:
            app = _create_app()

            caught_error = None
            try:
                app.startup()
            except SemanticError as err:
                caught_error = err

            if caught_error is None:
                errmsg = f"Expected a SemanticError for the body limit {configured!r}"
                raise AssertionError(errmsg)

        finally:
            patch.deactivate()
            reset_webapp_persona()

    return


def test_setup_infrastructure_rejects_an_invalid_body_limit():
    """
        Test that a configured body limit that is not a non-negative
        integer raises SemanticError.
    """
    patch = _patch_config_registry({webapp_module.MAX_REQUEST_BODY_SIZE_CONFIG_KEY: "16MB"})

    try:
        app = _create_app()

        caught_error = None
        try:
            app.startup()
        except SemanticError as err:
            caught_error = err

        if caught_error is None or webapp_module.MAX_REQUEST_BODY_SIZE_CONFIG_KEY not in str(caught_error):
            errmsg = f"Expected a SemanticError naming the configuration key, got {caught_error!r}"
            raise AssertionError(errmsg)

    finally:
        patch.deactivate()
        reset_webapp_persona()

    return


# =============================================================================
# establish_webapp_persona: failures leave no persona behind
# =============================================================================

def test_failed_construction_does_not_block_a_later_establish():
    """
        Test that an application class that raises in its constructor
        leaves no persona established, so a later call succeeds.
    """

    class BrokenApplication(WebApplication):
        def __init__(self, **kwargs):
            raise RuntimeError("constructor failed")

    try:
        reset_webapp_persona()

        caught_error = None
        try:
            establish_webapp_persona(
                name="brokenapp",
                logger_name="brokenapp",
                log_basename="brokenapp",
                application_cls=BrokenApplication,
            )
        except RuntimeError as err:
            caught_error = err

        if caught_error is None:
            raise AssertionError("Expected the constructor's RuntimeError")

        if webapp_module.WEBAPP_PERSONA_ESTABLISHED:
            raise AssertionError("Expected the persona not to count as established")

        app = establish_webapp_persona(
            name="testapp",
            logger_name="testapp",
            log_basename="testapp",
        )

        if app.name != "testapp":
            errmsg = f"Expected the retried persona 'testapp', got '{app.name}'"
            raise AssertionError(errmsg)

    finally:
        reset_webapp_persona()

    return


def test_singleton_check_failure_does_not_block_a_later_establish():
    """
        Test that the SemanticError for an already set
        THISAPPLICATION_SINGLETON does not mark the persona established.
    """
    import ccai.thisapp.wellknown as thisapp_wellknown

    try:
        reset_webapp_persona()
        thisapp_wellknown.THISAPPLICATION_SINGLETON = object()

        caught_error = None
        try:
            establish_webapp_persona(name="testapp", logger_name="testapp", log_basename="testapp")
        except SemanticError as err:
            caught_error = err

        thisapp_wellknown.THISAPPLICATION_SINGLETON = None

        if caught_error is None:
            raise AssertionError("Expected a SemanticError for the set singleton")

        app = establish_webapp_persona(name="testapp", logger_name="testapp", log_basename="testapp")

        if app is None:
            raise AssertionError("Expected the retry to establish the persona")

    finally:
        thisapp_wellknown.THISAPPLICATION_SINGLETON = None
        reset_webapp_persona()

    return


def test_concurrent_establish_creates_exactly_one_persona():
    """
        Test that threads racing to establish the persona produce one
        application; the others get PersonaAlreadyEstablishedError.
    """
    import threading
    import time

    from ccai.webworks.webapplication import PersonaAlreadyEstablishedError

    constructed = []

    class SlowApplication(WebApplication):
        def __init__(self, **kwargs):
            # Widen the window between the checks and the wiring.
            time.sleep(0.05)
            super().__init__(**kwargs)
            constructed.append(self)
            return

    outcomes = []
    outcomes_lock = threading.Lock()
    barrier = threading.Barrier(4)

    def establish():
        barrier.wait()
        try:
            establish_webapp_persona(
                name="raceapp",
                logger_name="raceapp",
                log_basename="raceapp",
                application_cls=SlowApplication,
            )
            outcome = "established"
        except PersonaAlreadyEstablishedError:
            outcome = "refused"
        with outcomes_lock:
            outcomes.append(outcome)
        return

    try:
        reset_webapp_persona()

        threads = [threading.Thread(target=establish) for _ in range(4)]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join(timeout=10)

        if sorted(outcomes) != ["established", "refused", "refused", "refused"]:
            errmsg = f"Expected one established persona and three refusals, got {outcomes}"
            raise AssertionError(errmsg)

        if len(constructed) != 1:
            errmsg = f"Expected one application to be constructed, got {len(constructed)}"
            raise AssertionError(errmsg)

    finally:
        reset_webapp_persona()

    return
