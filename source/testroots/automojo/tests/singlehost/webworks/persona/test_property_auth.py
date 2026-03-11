"""
.. module:: test_property_auth
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: Property-based tests for the WebApplication authentication
        management APIs: ``register_authenticator`` and
        ``configure_auth_middleware``.  Each property test uses the testbase
        ``@given`` decorator to verify that universal properties hold across
        generated inputs.

.. moduleauthor:: Automation Mojo LLC
"""

__author__ = "Automation Mojo LLC"
__copyright__ = "Copyright 2025, Automation Mojo LLC"
__credits__ = []

import automojo.testbase as testbase

from automojo.testbase.properties import given
from automojo.testbase.properties import strategies as st
from automojo.testbase.properties.strategies import composite

from automojo.testbase.mocking import Mock, create_module_patch

import automojo.webworks.webapplication as webapp_module

from automojo.webworks.webapplication import (
    establish_webapp_persona,
    reset_webapp_persona,
)
from automojo.webworks.persona.lifecycle import LifecyclePhase


# =============================================================================
# Strategies
# =============================================================================

scheme_strategy = st.text(
    alphabet="abcdefghijklmnopqrstuvwxyz",
    min_size=4,
    max_size=12,
)

path_segment_strategy = st.text(
    alphabet="abcdefghijklmnopqrstuvwxyz",
    min_size=3,
    max_size=10,
)

realm_strategy = st.text(
    alphabet="abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789 ",
    min_size=4,
    max_size=16,
).map(lambda s: s.strip() or "Realm")

priority_strategy = st.integers(0, 100)


@composite
def random_path_strategy(draw):
    """Generate a random valid URL path with 1 to 3 segments."""
    depth = draw(st.integers(1, 3))
    segments = [draw(path_segment_strategy) for _ in range(depth)]
    return "/" + "/".join(segments)


@composite
def path_set_strategy(draw, min_size=0, max_size=5):
    """Generate a set of random URL paths."""
    count = draw(st.integers(min_size, max_size))
    paths = set()
    for _ in range(count):
        paths.add(draw(random_path_strategy()))
    return paths


# =============================================================================
# Helpers
# =============================================================================

def _create_mock_authenticator(scheme_name):
    """
        Creates a mock Authenticator with the given scheme name.

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

@given(
    iteration=st.integers(0, 999),
    scheme_suffix=scheme_strategy,
    priority=priority_strategy,
    constraints={"max_examples": 10},
)
def test_property_register_authenticator_delegates_to_auth_system(iteration, scheme_suffix, priority):
    """
        Property 8: register_authenticator delegates to AuthenticationSystem

        For any Authenticator instance and priority integer, calling
        ``register_authenticator`` on the WebApplication shall result
        in the AuthenticationSystem containing that authenticator
        retrievable by its scheme, and the scheme appearing in the
        registered schemes list.

        **Feature: webapp-lifecycle, Property 8: register_authenticator delegates to AuthenticationSystem**
        **Validates: Requirements 7.2**
    """
    patch = None

    try:
        reset_webapp_persona()

        app = establish_webapp_persona(
            name="testapp",
            logger_name="testapp",
            log_basename="testapp",
        )

        patch = _advance_to_authentication_ready(app)

        scheme_name = f"scheme_{scheme_suffix}_{iteration}"

        mock_auth = _create_mock_authenticator(scheme_name)

        app.register_authenticator(mock_auth, priority=priority)

        retrieved = app._auth_system.get_authenticator(scheme_name)

        testbase.assert_true(
            retrieved is mock_auth,
            f"Expected get_authenticator('{scheme_name}') to return the "
            f"registered mock authenticator, got {type(retrieved).__name__}"
        )

        registered_schemes = app._auth_system.get_registered_schemes()

        testbase.assert_true(
            scheme_name in registered_schemes,
            f"Expected scheme '{scheme_name}' to appear in registered schemes "
            f"{registered_schemes}"
        )

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

@given(
    exclude_paths=path_set_strategy(min_size=0, max_size=5),
    optional_paths=path_set_strategy(min_size=0, max_size=3),
    realm=realm_strategy,
    constraints={"max_examples": 10},
)
def test_property_configure_auth_middleware_creates_wired_middleware(exclude_paths, optional_paths, realm):
    """
        Property 9: configure_auth_middleware creates properly wired middleware

        For any set of exclude paths, optional paths, policies, and
        realm string, calling ``configure_auth_middleware`` after
        infrastructure setup shall return an AuthenticationMiddleware
        whose ``app`` property is the WebApplication's ``asgi_app``
        and whose ``auth_system`` property is the WebApplication's
        ``auth_system``.

        **Feature: webapp-lifecycle, Property 9: configure_auth_middleware creates properly wired middleware**
        **Validates: Requirements 7.3**
    """
    patch = None

    try:
        reset_webapp_persona()

        app = establish_webapp_persona(
            name="testapp",
            logger_name="testapp",
            log_basename="testapp",
        )

        patch = _startup_app(app)

        middleware = app.configure_auth_middleware(
            exclude_paths=exclude_paths,
            optional_paths=optional_paths,
            realm=realm,
        )

        testbase.assert_true(
            middleware.app is app._asgi_app,
            f"Expected middleware.app to be the same object as app._asgi_app "
            f"(identity check failed)"
        )

        testbase.assert_true(
            middleware.auth_system is app._auth_system,
            f"Expected middleware.auth_system to be the same object as "
            f"app._auth_system (identity check failed)"
        )

        testbase.assert_equal(
            middleware.realm, realm,
            f"Expected middleware.realm to be '{realm}', got '{middleware.realm}'"
        )

        for ep in exclude_paths:
            testbase.assert_true(
                ep in middleware.exclude_paths,
                f"Expected '{ep}' to be in middleware.exclude_paths "
                f"{middleware.exclude_paths}"
            )

        for op in optional_paths:
            testbase.assert_true(
                op in middleware.optional_paths,
                f"Expected '{op}' to be in middleware.optional_paths "
                f"{middleware.optional_paths}"
            )

    finally:
        if patch is not None:
            patch.deactivate()
        reset_webapp_persona()

    return


if __name__ == "__main__":
    from automojo.testbase.entrypoints import generic_test_entrypoint
    generic_test_entrypoint()
