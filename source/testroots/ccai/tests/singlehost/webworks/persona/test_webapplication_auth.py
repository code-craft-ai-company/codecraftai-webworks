"""
.. module:: test_webapplication_auth
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: Unit tests for the WebApplication authentication management
        APIs: ``register_authenticator`` and ``configure_auth_middleware``.

.. moduleauthor:: Code Craft AI LLC
"""

__author__ = "Code Craft AI LLC"
__copyright__ = "Copyright 2025, Code Craft AI LLC"
__credits__ = []


import ccai.webworks.webapplication as webapp_module

from ccai.testbase.mocking import Mock, create_module_patch

from ccai.webworks.webapplication import (
    establish_webapp_persona,
    reset_webapp_persona,
)
from ccai.webworks.persona.lifecycle import LifecycleError, LifecyclePhase


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


def _startup_app(app):
    """
        Runs the full startup sequence on the given WebApplication
        with ManagedConfigRegistry mocked to avoid filesystem access.

        :param app: The WebApplication instance to start up.

        :returns: The patch object so the caller can deactivate it.
    """
    mock_registry_instance = Mock()
    mock_registry_instance.configure(recursive=True)

    patch = create_module_patch(webapp_module, "ManagedConfigRegistry")
    mock_cls = patch.activate()
    mock_cls.configure(return_value=mock_registry_instance)

    app.startup()

    return patch


def _advance_to_authentication_ready(app):
    """
        Advances the given WebApplication through all lifecycle phases
        up to and including ``AUTHENTICATION_READY`` by mocking
        ManagedConfigRegistry and calling each setup method in order.

        This intentionally does NOT call ``setup_infrastructure`` so
        the application remains at ``AUTHENTICATION_READY``.

        :param app: The WebApplication instance to advance.

        :returns: The patch object so the caller can deactivate it.
    """
    mock_registry_instance = Mock()
    mock_registry_instance.configure(recursive=True)

    patch = create_module_patch(webapp_module, "ManagedConfigRegistry")
    mock_cls = patch.activate()
    mock_cls.configure(return_value=mock_registry_instance)

    app.setup_configuration()
    app.setup_credentials()
    app.setup_data_profiles()
    app.setup_database()
    app.setup_authentication()

    return patch


# =============================================================================
# Unit Tests for register_authenticator
# =============================================================================

def test_register_authenticator_adds_authenticator_to_auth_system():
    """
        Test that ``register_authenticator`` delegates to the
        AuthenticationSystem and the authenticator becomes retrievable
        by its scheme via ``get_authenticator``.

        _Requirements: 7.2_
    """
    app = _create_app()
    patch = None

    try:
        patch = _advance_to_authentication_ready(app)

        mock_auth = Mock()
        mock_auth.configure(recursive=True)
        mock_auth.mock_context().set_attribute("scheme", "bearer")
        mock_auth.mock_context().mock_method("can_handle", return_value=True)

        app.register_authenticator(mock_auth, priority=10)

        retrieved = app._auth_system.get_authenticator("bearer")

        if retrieved is not mock_auth:
            errmsg = (
                "Expected get_authenticator('bearer') to return the "
                "registered mock authenticator, got "
                f"{type(retrieved)}"
            )
            raise AssertionError(errmsg)

    finally:
        if patch is not None:
            patch.deactivate()
        reset_webapp_persona()

    return


# =============================================================================
# Unit Tests for configure_auth_middleware
# =============================================================================

def test_configure_auth_middleware_creates_middleware_with_correct_properties():
    """
        Test that ``configure_auth_middleware`` creates an
        AuthenticationMiddleware whose ``app`` property returns the
        WebApplication's ASGIApplication and whose ``auth_system``
        property returns the WebApplication's AuthenticationSystem.

        _Requirements: 7.3_
    """
    app = _create_app()
    patch = None

    try:
        patch = _startup_app(app)

        middleware = app.configure_auth_middleware(
            exclude_paths={"/health"},
            realm="TestRealm",
        )

        if middleware.app is not app._asgi_app:
            errmsg = (
                "Expected middleware.app to be the same object as "
                "app._asgi_app"
            )
            raise AssertionError(errmsg)

        if middleware.auth_system is not app._auth_system:
            errmsg = (
                "Expected middleware.auth_system to be the same object "
                "as app._auth_system"
            )
            raise AssertionError(errmsg)

        if middleware.realm != "TestRealm":
            errmsg = (
                f"Expected middleware.realm to be 'TestRealm', "
                f"got '{middleware.realm}'"
            )
            raise AssertionError(errmsg)

        if "/health" not in middleware.exclude_paths:
            errmsg = (
                "Expected '/health' to be in middleware.exclude_paths, "
                f"got {middleware.exclude_paths}"
            )
            raise AssertionError(errmsg)

    finally:
        if patch is not None:
            patch.deactivate()
        reset_webapp_persona()

    return


def test_configure_auth_middleware_before_infrastructure_raises_lifecycle_error():
    """
        Test that calling ``configure_auth_middleware`` before the
        application has reached the ``INFRASTRUCTURE_READY`` phase
        raises a ``LifecycleError`` with a descriptive message.

        _Requirements: 7.4_
    """
    app = _create_app()
    patch = None

    try:
        patch = _advance_to_authentication_ready(app)

        # The app is at AUTHENTICATION_READY, not INFRASTRUCTURE_READY
        caught_error = None

        try:
            app.configure_auth_middleware(
                exclude_paths={"/health"},
                realm="TestRealm",
            )
        except LifecycleError as err:
            caught_error = err

        if caught_error is None:
            errmsg = (
                "Expected LifecycleError when calling "
                "configure_auth_middleware before INFRASTRUCTURE_READY"
            )
            raise AssertionError(errmsg)

        error_message = str(caught_error)

        if "infrastructure_ready" not in error_message.lower():
            errmsg = (
                "Expected LifecycleError message to reference "
                "'infrastructure_ready', got: "
                f"{error_message}"
            )
            raise AssertionError(errmsg)

        if "configure_auth_middleware" not in error_message:
            errmsg = (
                "Expected LifecycleError message to reference "
                "'configure_auth_middleware', got: "
                f"{error_message}"
            )
            raise AssertionError(errmsg)

        if caught_error.required_phase != LifecyclePhase.INFRASTRUCTURE_READY:
            errmsg = (
                "Expected required_phase to be INFRASTRUCTURE_READY, "
                f"got {caught_error.required_phase}"
            )
            raise AssertionError(errmsg)

        if caught_error.current_phase != LifecyclePhase.AUTHENTICATION_READY:
            errmsg = (
                "Expected current_phase to be AUTHENTICATION_READY, "
                f"got {caught_error.current_phase}"
            )
            raise AssertionError(errmsg)

    finally:
        if patch is not None:
            patch.deactivate()
        reset_webapp_persona()

    return
