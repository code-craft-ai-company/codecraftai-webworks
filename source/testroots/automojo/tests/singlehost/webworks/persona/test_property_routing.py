"""
.. module:: test_property_routing
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: Property-based tests for the WebApplication endpoint
        registration APIs: ``attach_route`` and
        ``attach_blueprint_to_route``.  Each property test iterates over
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
from automojo.webworks.persona.lifecycle import (
    EndpointConflictError,
    BlueprintAlreadyRegisteredError,
)
from automojo.webworks.routing.request import Request


# =============================================================================
# Helpers
# =============================================================================

HTTP_METHODS = ["GET", "POST", "PUT", "DELETE", "PATCH"]


def _random_segment(min_length=3, max_length=10):
    """
        Generate a random lowercase alphabetic URL path segment.

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
    segments = [_random_segment() for _ in range(depth)]
    path = "/" + "/".join(segments)
    return path


def _random_method():
    """
        Select a random HTTP method from the standard set.

        :returns: A random HTTP method string.
    """
    return random.choice(HTTP_METHODS)


def _random_name(min_length=3, max_length=12):
    """
        Generate a random lowercase alphabetic name suitable for use as
        a function name or docstring word.

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

    patch = create_module_patch(webapp_module, "ManagedConfigRegistry")
    mock_cls = patch.activate()
    mock_registry = Mock()
    mock_registry.configure(recursive=True)
    mock_cls.configure(return_value=mock_registry)

    return app, patch



# =============================================================================
# Property 3: attach_route registers routable endpoints
# Feature: webapp-lifecycle, Property 3: attach_route registers routable endpoints
# Validates: Requirements 2.1
# =============================================================================

def test_property_attach_route_registers_routable_endpoints():
    """
        Property 3: attach_route registers routable endpoints

        For any valid URL path string and HTTP method, applying the
        ``attach_route`` decorator to a handler function and then calling
        ``startup()`` shall result in the Router successfully matching a
        request to that path and method to the decorated handler.

        Each iteration generates a unique random path and a random HTTP
        method, registers a handler via ``attach_route``, starts the
        application, and verifies the Router matches the path and method
        to the correct handler.  Runs 10 iterations.

        **Feature: webapp-lifecycle, Property 3: attach_route registers routable endpoints**
        **Validates: Requirements 2.1**
    """
    for iteration in range(10):
        patch = None

        try:
            reset_webapp_persona()

            # Generate a unique path per iteration to avoid conflicts
            path = f"/prop3/{_random_segment()}/{iteration}"
            method = _random_method()

            app = establish_webapp_persona(
                name="testapp",
                logger_name="testapp",
                log_basename="testapp",
            )

            # Define a handler and register it via attach_route
            def handler_func(request):
                return {"ok": True}

            decorated = app.attach_route(path, methods=[method])(handler_func)

            # Patch ManagedConfigRegistry and start up
            patch = create_module_patch(webapp_module, "ManagedConfigRegistry")
            mock_cls = patch.activate()
            mock_registry = Mock()
            mock_registry.configure(recursive=True)
            mock_cls.configure(return_value=mock_registry)

            app.startup()

            # Verify the Router matches the path and method
            request = Request(method=method, path=path)
            match = app.router.match(request)

            if match is None:
                errmsg = (
                    f"Iteration {iteration}: Router did not match "
                    f"{method} {path} after attach_route and startup"
                )
                raise AssertionError(errmsg)

            if match.handler is not decorated:
                errmsg = (
                    f"Iteration {iteration}: Router matched {method} {path} "
                    f"to handler {match.handler}, expected the decorated "
                    f"handler {decorated}"
                )
                raise AssertionError(errmsg)

        finally:
            if patch is not None:
                patch.deactivate()
            reset_webapp_persona()

    return


# =============================================================================
# Property 4: attach_route conflict detection
# Feature: webapp-lifecycle, Property 4: attach_route conflict detection
# Validates: Requirements 2.2
# =============================================================================

def test_property_attach_route_conflict_detection():
    """
        Property 4: attach_route conflict detection

        For any URL path and HTTP method, if ``attach_route`` is used to
        register a handler at that path and method, then using
        ``attach_route`` again with the same path and method shall raise
        an ``EndpointConflictError``.

        Each iteration generates a random path and method, registers a
        handler, starts the application so the route is live in the
        Router, then attempts to register a second handler at the same
        path and method.  Runs 10 iterations.

        **Feature: webapp-lifecycle, Property 4: attach_route conflict detection**
        **Validates: Requirements 2.2**
    """
    for iteration in range(10):
        patch = None

        try:
            reset_webapp_persona()

            path = f"/prop4/{_random_segment()}/{iteration}"
            method = _random_method()

            app = establish_webapp_persona(
                name="testapp",
                logger_name="testapp",
                log_basename="testapp",
            )

            # Register the first handler before startup (queued)
            @app.attach_route(path, methods=[method])
            def first_handler(request):
                return {"first": True}

            # Patch ManagedConfigRegistry and start up
            patch = create_module_patch(webapp_module, "ManagedConfigRegistry")
            mock_cls = patch.activate()
            mock_registry = Mock()
            mock_registry.configure(recursive=True)
            mock_cls.configure(return_value=mock_registry)

            app.startup()

            # Attempt to register a second handler at the same path+method
            caught_error = None

            try:
                @app.attach_route(path, methods=[method])
                def second_handler(request):
                    return {"second": True}
            except EndpointConflictError as err:
                caught_error = err

            if caught_error is None:
                errmsg = (
                    f"Iteration {iteration}: Expected EndpointConflictError "
                    f"when registering duplicate route {method} {path}, "
                    f"but no error was raised"
                )
                raise AssertionError(errmsg)

            error_message = str(caught_error)

            if path not in error_message:
                errmsg = (
                    f"Iteration {iteration}: EndpointConflictError message "
                    f"does not contain path '{path}'. Got: '{error_message}'"
                )
                raise AssertionError(errmsg)

            if method not in error_message:
                errmsg = (
                    f"Iteration {iteration}: EndpointConflictError message "
                    f"does not contain method '{method}'. Got: '{error_message}'"
                )
                raise AssertionError(errmsg)

        finally:
            if patch is not None:
                patch.deactivate()
            reset_webapp_persona()

    return


# =============================================================================
# Property 5: attach_route preserves function metadata
# Feature: webapp-lifecycle, Property 5: attach_route preserves function metadata
# Validates: Requirements 2.3
# =============================================================================

def test_property_attach_route_preserves_function_metadata():
    """
        Property 5: attach_route preserves function metadata

        For any function with a ``__name__`` and ``__doc__`` attribute,
        after applying the ``attach_route`` decorator, the returned
        function shall have the same ``__name__`` and ``__doc__`` as the
        original.

        Each iteration creates a function, assigns random ``__name__``
        and ``__doc__`` values, applies ``attach_route``, and verifies
        both attributes are preserved.  Runs 10 iterations.

        **Feature: webapp-lifecycle, Property 5: attach_route preserves function metadata**
        **Validates: Requirements 2.3**
    """
    for iteration in range(10):
        try:
            reset_webapp_persona()

            app = establish_webapp_persona(
                name="testapp",
                logger_name="testapp",
                log_basename="testapp",
            )

            # Generate random metadata
            random_name = f"handler_{_random_name()}"
            random_doc = f"Docstring for {_random_name()} iteration {iteration}."

            # Create a function with the random metadata
            def original_func(request):
                return {"iteration": iteration}

            original_func.__name__ = random_name
            original_func.__doc__ = random_doc

            # Use a unique path per iteration to avoid conflicts
            path = f"/prop5/{_random_segment()}/{iteration}"
            method = _random_method()

            decorated = app.attach_route(path, methods=[method])(original_func)

            # Verify __name__ is preserved
            if decorated.__name__ != random_name:
                errmsg = (
                    f"Iteration {iteration}: Expected decorated __name__ "
                    f"'{random_name}', got '{decorated.__name__}'"
                )
                raise AssertionError(errmsg)

            # Verify __doc__ is preserved
            if decorated.__doc__ != random_doc:
                errmsg = (
                    f"Iteration {iteration}: Expected decorated __doc__ "
                    f"'{random_doc}', got '{decorated.__doc__}'"
                )
                raise AssertionError(errmsg)

        finally:
            reset_webapp_persona()

    return



# =============================================================================
# Property 6: attach_blueprint_to_route registers all blueprint endpoints
# Feature: webapp-lifecycle, Property 6: attach_blueprint_to_route registers all blueprint endpoints
# Validates: Requirements 3.1, 3.3
# =============================================================================

def test_property_attach_blueprint_registers_all_endpoints():
    """
        Property 6: attach_blueprint_to_route registers all blueprint endpoints

        For any ``RestBlueprint`` subclass with registered endpoints,
        calling ``attach_blueprint_to_route`` and then ``startup()``
        shall result in the blueprint's ``register`` method being called
        with the application's Router.

        Each iteration creates a fake blueprint class with a tracking
        ``register`` classmethod, registers it via
        ``attach_blueprint_to_route`` before startup, starts the
        application, and verifies that ``register`` was called with the
        correct Router instance.  Runs 10 iterations.

        **Feature: webapp-lifecycle, Property 6: attach_blueprint_to_route registers all blueprint endpoints**
        **Validates: Requirements 3.1, 3.3**
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

            # Create a unique fake blueprint class per iteration so that
            # each is a distinct class object (avoids duplicate detection
            # across iterations sharing the same singleton).
            register_calls = []

            # Use type() to create a unique class each iteration
            def make_register(calls_list):
                @classmethod
                def register(cls, router=None):
                    calls_list.append(router)
                return register

            blueprint_cls = type(
                f"FakeBlueprint_{iteration}",
                (),
                {"register": make_register(register_calls)},
            )

            # Register the blueprint before startup (queued)
            app.attach_blueprint_to_route(blueprint_cls)

            # Verify it was queued, not yet called
            if len(register_calls) != 0:
                errmsg = (
                    f"Iteration {iteration}: Expected register to not be "
                    f"called before startup, got {len(register_calls)} calls"
                )
                raise AssertionError(errmsg)

            # Patch ManagedConfigRegistry and start up
            patch = create_module_patch(webapp_module, "ManagedConfigRegistry")
            mock_cls = patch.activate()
            mock_registry = Mock()
            mock_registry.configure(recursive=True)
            mock_cls.configure(return_value=mock_registry)

            app.startup()

            # Verify register was called exactly once with the app's router
            if len(register_calls) != 1:
                errmsg = (
                    f"Iteration {iteration}: Expected register to be called "
                    f"once during startup, got {len(register_calls)} calls"
                )
                raise AssertionError(errmsg)

            if register_calls[0] is not app._router:
                errmsg = (
                    f"Iteration {iteration}: Expected register to be called "
                    f"with the app's Router instance"
                )
                raise AssertionError(errmsg)

        finally:
            if patch is not None:
                patch.deactivate()
            reset_webapp_persona()

    return


# =============================================================================
# Property 7: Duplicate blueprint registration raises error
# Feature: webapp-lifecycle, Property 7: Duplicate blueprint registration raises error
# Validates: Requirements 3.2
# =============================================================================

def test_property_duplicate_blueprint_registration_raises_error():
    """
        Property 7: Duplicate blueprint registration raises error

        For any ``RestBlueprint`` subclass, calling
        ``attach_blueprint_to_route`` twice with the same class shall
        raise a ``BlueprintAlreadyRegisteredError`` on the second call.

        Each iteration creates a unique fake blueprint class, registers
        it once successfully, then attempts a second registration and
        verifies the error is raised with the correct blueprint class
        reference.  Runs 10 iterations.

        **Feature: webapp-lifecycle, Property 7: Duplicate blueprint registration raises error**
        **Validates: Requirements 3.2**
    """
    for iteration in range(10):
        try:
            reset_webapp_persona()

            app = establish_webapp_persona(
                name="testapp",
                logger_name="testapp",
                log_basename="testapp",
            )

            # Create a unique fake blueprint class per iteration
            blueprint_name = f"FakeBlueprint_{iteration}"

            blueprint_cls = type(
                blueprint_name,
                (),
                {
                    "register": classmethod(lambda cls, router=None: None),
                },
            )

            # First registration should succeed
            app.attach_blueprint_to_route(blueprint_cls)

            # Second registration should raise BlueprintAlreadyRegisteredError
            caught_error = None

            try:
                app.attach_blueprint_to_route(blueprint_cls)
            except BlueprintAlreadyRegisteredError as err:
                caught_error = err

            if caught_error is None:
                errmsg = (
                    f"Iteration {iteration}: Expected "
                    f"BlueprintAlreadyRegisteredError when registering "
                    f"'{blueprint_name}' twice, but no error was raised"
                )
                raise AssertionError(errmsg)

            if caught_error.blueprint_cls is not blueprint_cls:
                errmsg = (
                    f"Iteration {iteration}: Expected "
                    f"BlueprintAlreadyRegisteredError.blueprint_cls to "
                    f"reference the duplicate class '{blueprint_name}'"
                )
                raise AssertionError(errmsg)

            error_message = str(caught_error)

            if blueprint_name not in error_message:
                errmsg = (
                    f"Iteration {iteration}: Expected error message to "
                    f"contain '{blueprint_name}', got: '{error_message}'"
                )
                raise AssertionError(errmsg)

        finally:
            reset_webapp_persona()

    return
