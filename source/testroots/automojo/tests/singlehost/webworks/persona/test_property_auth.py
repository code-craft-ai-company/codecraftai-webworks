"""
.. module:: test_property_auth
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: Property-based tests for the WebApplication authentication
        management APIs: ``register_authenticator`` and
        ``configure_auth_middleware``.  Each property test iterates over
        generated inputs a minimum of 10 times to verify that universal
        properties hold across all valid executions.

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
    establish_webapp_persona,
    reset_webapp_persona,
)
from automojo.webworks.persona.lifecycle import LifecyclePhase


# =============================================================================
# Helpers
# =============================================================================

def _random_scheme(min_length=4, max_length=12):
    """
        Generate a random lowercase alphabetic scheme name suitable
        for use as an authentication scheme identifier.

        :returns: A random string of lowercase letters.
    """
    length = random.randint(min_length, max_length)
    return "".join(random.choices(string.ascii_lowercase, k=length))


def _random_path():
    """
        Generate a random valid URL path with 1 to 3 segments.

        :returns: A random URL path string like ``/api/abcdef``.
    """
    depth = random.randint(1, 3)
    segments = []
    for _ in range(depth):
        seg_length = random.randint(3, 10)
        seg = "".join(random.choices(string.ascii_lowercase, k=seg_length))
        segments.append(seg)
    path = "/" + "/".join(segments)
    return path


def _random_realm(min_length=4, max_length=16):
    """
        Generate a random realm string containing alphanumeric
        characters and spaces.

        :returns: A random realm string.
    """
    length = random.randint(min_length, max_length)
    chars = string.ascii_letters + string.digits + " "
    return "".join(random.choices(chars, k=length)).strip() or "Realm"


def _random_priority():
    """
        Generate a random integer priority value between 0 and 100.

        :returns: A random integer.
    """
    return random.randint(0, 100)


def _create_mock_authenticator(scheme_name):
    """
        Creates a mock Authenticator with the given scheme name.

        The mock is configured with a ``scheme`` attribute and a
        ``can_handle`` method that returns ``True``.

        :param scheme_name: The scheme identifier for the mock.

        :returns: A configured Mock instance.
    """
    mock_auth = Mock()
    mock_auth.configure(recursive=True)
    mock_auth.mock_context().set_attribute("scheme", scheme_name)
    mock_auth.mock_context().mock_method("can_handle", return_value=True)

    return mock_auth


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


# =============================================================================
# Property 8: register_authenticator delegates to AuthenticationSystem
# Feature: webapp-lifecycle, Property 8: register_authenticator delegates to AuthenticationSystem
# Validates: Requirements 7.2
# =============================================================================

def test_property_register_authenticator_delegates_to_auth_system():
    """
        Property 8: register_authenticator delegates to AuthenticationSystem

        For any Authenticator instance and priority integer, calling
        ``register_authenticator`` on the WebApplication shall result
        in the AuthenticationSystem containing that authenticator
        retrievable by its scheme, and the scheme appearing in the
        registered schemes list.

        Each iteration generates a mock authenticator with a random
        scheme name and a random priority, registers it via
        ``register_authenticator``, and verifies the AuthenticationSystem
        contains the authenticator by scheme and that the scheme appears
        in the registered schemes list.  Runs 10 iterations.

        **Feature: webapp-lifecycle, Property 8: register_authenticator delegates to AuthenticationSystem**
        **Validates: Requirements 7.2**
    """
    for iteration in range(10):
        patch = None

        try:
            reset_webapp_persona()

            app = establish_webapp_persona(
                name="testapp",
                logger_name="testapp",
                log_basename="testapp",
            )

            patch = _advance_to_authentication_ready(app)

            # Generate a random scheme name and priority
            scheme_name = f"scheme_{_random_scheme()}_{iteration}"
            priority = _random_priority()

            # Create a mock authenticator with the random scheme
            mock_auth = _create_mock_authenticator(scheme_name)

            # Register the authenticator
            app.register_authenticator(mock_auth, priority=priority)

            # Verify the authenticator is retrievable by scheme
            retrieved = app._auth_system.get_authenticator(scheme_name)

            if retrieved is not mock_auth:
                errmsg = (
                    f"Iteration {iteration}: Expected "
                    f"get_authenticator('{scheme_name}') to return the "
                    f"registered mock authenticator, got "
                    f"{type(retrieved).__name__}"
                )
                raise AssertionError(errmsg)

            # Verify the scheme appears in the registered schemes list
            registered_schemes = app._auth_system.get_registered_schemes()

            if scheme_name not in registered_schemes:
                errmsg = (
                    f"Iteration {iteration}: Expected scheme "
                    f"'{scheme_name}' to appear in registered schemes "
                    f"{registered_schemes}"
                )
                raise AssertionError(errmsg)

        finally:
            if patch is not None:
                patch.deactivate()
            reset_webapp_persona()

    return


# =============================================================================
# Property 9: configure_auth_middleware creates properly wired middleware
# Feature: webapp-lifecycle, Property 9: configure_auth_middleware creates properly wired middleware
# Validates: Requirements 7.3
# =============================================================================

def test_property_configure_auth_middleware_creates_wired_middleware():
    """
        Property 9: configure_auth_middleware creates properly wired middleware

        For any set of exclude paths, optional paths, policies, and
        realm string, calling ``configure_auth_middleware`` after
        infrastructure setup shall return an AuthenticationMiddleware
        whose ``app`` property is the WebApplication's ``asgi_app``
        and whose ``auth_system`` property is the WebApplication's
        ``auth_system``.

        Each iteration generates random exclude paths, optional paths,
        and a realm string, calls ``configure_auth_middleware`` after
        full startup, and verifies the returned middleware's ``app``
        and ``auth_system`` properties match the WebApplication's
        internal references.  Runs 10 iterations.

        **Feature: webapp-lifecycle, Property 9: configure_auth_middleware creates properly wired middleware**
        **Validates: Requirements 7.3**
    """
    for iteration in range(10):
        patch = None

        try:
            reset_webapp_persona()

            app = establish_webapp_persona(
                name="testapp",
                logger_name="testapp",
                log_basename="testapp",
            )

            patch = _startup_app(app)

            # Generate random exclude paths (0 to 5 paths)
            num_exclude = random.randint(0, 5)
            exclude_paths = set()
            for _ in range(num_exclude):
                exclude_paths.add(_random_path())

            # Generate random optional paths (0 to 3 paths)
            num_optional = random.randint(0, 3)
            optional_paths = set()
            for _ in range(num_optional):
                optional_paths.add(_random_path())

            # Generate a random realm string
            realm = _random_realm()

            # Call configure_auth_middleware
            middleware = app.configure_auth_middleware(
                exclude_paths=exclude_paths,
                optional_paths=optional_paths,
                realm=realm,
            )

            # Verify middleware.app is the same object as app._asgi_app
            if middleware.app is not app._asgi_app:
                errmsg = (
                    f"Iteration {iteration}: Expected middleware.app to be "
                    f"the same object as app._asgi_app (identity check "
                    f"failed)"
                )
                raise AssertionError(errmsg)

            # Verify middleware.auth_system is the same object as
            # app._auth_system
            if middleware.auth_system is not app._auth_system:
                errmsg = (
                    f"Iteration {iteration}: Expected "
                    f"middleware.auth_system to be the same object as "
                    f"app._auth_system (identity check failed)"
                )
                raise AssertionError(errmsg)

            # Verify middleware.realm matches the provided realm
            if middleware.realm != realm:
                errmsg = (
                    f"Iteration {iteration}: Expected middleware.realm "
                    f"to be '{realm}', got '{middleware.realm}'"
                )
                raise AssertionError(errmsg)

            # Verify middleware.exclude_paths contains all provided paths
            for ep in exclude_paths:
                if ep not in middleware.exclude_paths:
                    errmsg = (
                        f"Iteration {iteration}: Expected '{ep}' to be "
                        f"in middleware.exclude_paths "
                        f"{middleware.exclude_paths}"
                    )
                    raise AssertionError(errmsg)

            # Verify middleware.optional_paths contains all provided paths
            for op in optional_paths:
                if op not in middleware.optional_paths:
                    errmsg = (
                        f"Iteration {iteration}: Expected '{op}' to be "
                        f"in middleware.optional_paths "
                        f"{middleware.optional_paths}"
                    )
                    raise AssertionError(errmsg)

        finally:
            if patch is not None:
                patch.deactivate()
            reset_webapp_persona()

    return
