"""
.. module:: test_property_routing
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: Property-based tests for the WebApplication endpoint
        registration APIs: ``attach_route`` and
        ``attach_blueprint_to_route``.  Each property test uses the testbase
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
from ccai.testbase.properties.strategies import composite

from ccai.testbase.mocking import Mock, create_module_patch

import ccai.webworks.webapplication as webapp_module

from ccai.webworks.webapplication import (
    establish_webapp_persona,
    reset_webapp_persona,
)
from ccai.webworks.persona.lifecycle import (
    EndpointConflictError,
    BlueprintAlreadyRegisteredError,
)
from ccai.webworks.routing.request import Request


# =============================================================================
# Strategies
# =============================================================================

HTTP_METHODS = ["GET", "POST", "PUT", "DELETE", "PATCH"]

segment_strategy = st.text(
    alphabet="abcdefghijklmnopqrstuvwxyz",
    min_size=3,
    max_size=10,
)

method_strategy = st.sampled_from(HTTP_METHODS)

name_strategy = st.text(
    alphabet="abcdefghijklmnopqrstuvwxyz",
    min_size=3,
    max_size=12,
)


@composite
def random_path_strategy(draw):
    """Generate a random valid URL path with 1 to 3 segments."""
    depth = draw(st.integers(1, 3))
    segments = [draw(segment_strategy) for _ in range(depth)]
    return "/" + "/".join(segments)


# =============================================================================
# Property 3: attach_route registers routable endpoints
# Feature: webapp-lifecycle, Property 3: attach_route registers routable endpoints
# Validates: Requirements 2.1
# =============================================================================

@given(
    iteration=st.integers(0, 9999),
    path_segment=segment_strategy,
    method=method_strategy,
    constraints={"max_examples": 10},
)
def test_property_attach_route_registers_routable_endpoints(iteration, path_segment, method):
    """
        Property 3: attach_route registers routable endpoints

        For any valid URL path string and HTTP method, applying the
        ``attach_route`` decorator to a handler function and then calling
        ``startup()`` shall result in the Router successfully matching a
        request to that path and method to the decorated handler.

        **Feature: webapp-lifecycle, Property 3: attach_route registers routable endpoints**
        **Validates: Requirements 2.1**
    """
    patch = None
    path = f"/prop3/{path_segment}/{iteration}"

    try:
        reset_webapp_persona()

        app = establish_webapp_persona(
            name="testapp",
            logger_name="testapp",
            log_basename="testapp",
        )

        def handler_func(request):
            return {"ok": True}

        decorated = app.attach_route(path, methods=[method])(handler_func)

        patch = create_module_patch(webapp_module, "ManagedConfigRegistry")
        mock_cls = patch.activate()
        mock_registry = Mock()
        mock_registry.configure(recursive=True)
        mock_cls.configure(return_value=mock_registry)

        app.startup()

        request = Request(method=method, path=path)
        match = app.router.match(request)

        testbase.assert_true(
            match is not None,
            f"Router did not match {method} {path} after attach_route and startup"
        )

        testbase.assert_true(
            match.handler is decorated,
            f"Router matched {method} {path} to handler {match.handler}, "
            f"expected the decorated handler {decorated}"
        )

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

@given(
    iteration=st.integers(0, 9999),
    path_segment=segment_strategy,
    method=method_strategy,
    constraints={"max_examples": 10},
)
def test_property_attach_route_conflict_detection(iteration, path_segment, method):
    """
        Property 4: attach_route conflict detection

        For any URL path and HTTP method, if ``attach_route`` is used to
        register a handler at that path and method, then using
        ``attach_route`` again with the same path and method shall raise
        an ``EndpointConflictError``.

        **Feature: webapp-lifecycle, Property 4: attach_route conflict detection**
        **Validates: Requirements 2.2**
    """
    patch = None
    path = f"/prop4/{path_segment}/{iteration}"

    try:
        reset_webapp_persona()

        app = establish_webapp_persona(
            name="testapp",
            logger_name="testapp",
            log_basename="testapp",
        )

        @app.attach_route(path, methods=[method])
        def first_handler(request):
            return {"first": True}

        patch = create_module_patch(webapp_module, "ManagedConfigRegistry")
        mock_cls = patch.activate()
        mock_registry = Mock()
        mock_registry.configure(recursive=True)
        mock_cls.configure(return_value=mock_registry)

        app.startup()

        caught_error = None

        try:
            @app.attach_route(path, methods=[method])
            def second_handler(request):
                return {"second": True}
        except EndpointConflictError as err:
            caught_error = err

        testbase.assert_true(
            caught_error is not None,
            f"Expected EndpointConflictError when registering duplicate route "
            f"{method} {path}, but no error was raised"
        )

        error_message = str(caught_error)

        testbase.assert_true(
            path in error_message,
            f"EndpointConflictError message does not contain path '{path}'. "
            f"Got: '{error_message}'"
        )

        testbase.assert_true(
            method in error_message,
            f"EndpointConflictError message does not contain method '{method}'. "
            f"Got: '{error_message}'"
        )

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

@given(
    iteration=st.integers(0, 9999),
    random_name=name_strategy,
    random_doc_word=name_strategy,
    path_segment=segment_strategy,
    method=method_strategy,
    constraints={"max_examples": 10},
)
def test_property_attach_route_preserves_function_metadata(iteration, random_name, random_doc_word, path_segment, method):
    """
        Property 5: attach_route preserves function metadata

        For any function with a ``__name__`` and ``__doc__`` attribute,
        after applying the ``attach_route`` decorator, the returned
        function shall have the same ``__name__`` and ``__doc__`` as the
        original.

        **Feature: webapp-lifecycle, Property 5: attach_route preserves function metadata**
        **Validates: Requirements 2.3**
    """
    try:
        reset_webapp_persona()

        app = establish_webapp_persona(
            name="testapp",
            logger_name="testapp",
            log_basename="testapp",
        )

        handler_name = f"handler_{random_name}"
        handler_doc = f"Docstring for {random_doc_word} iteration {iteration}."

        def original_func(request):
            return {"iteration": iteration}

        original_func.__name__ = handler_name
        original_func.__doc__ = handler_doc

        path = f"/prop5/{path_segment}/{iteration}"

        decorated = app.attach_route(path, methods=[method])(original_func)

        testbase.assert_equal(
            decorated.__name__, handler_name,
            f"Expected decorated __name__ '{handler_name}', got '{decorated.__name__}'"
        )

        testbase.assert_equal(
            decorated.__doc__, handler_doc,
            f"Expected decorated __doc__ '{handler_doc}', got '{decorated.__doc__}'"
        )

    finally:
        reset_webapp_persona()

    return


# =============================================================================
# Property 6: attach_blueprint_to_route registers all blueprint endpoints
# Feature: webapp-lifecycle, Property 6: attach_blueprint_to_route registers all blueprint endpoints
# Validates: Requirements 3.1, 3.3
# =============================================================================

@given(
    iteration=st.integers(0, 9999),
    constraints={"max_examples": 10},
)
def test_property_attach_blueprint_registers_all_endpoints(iteration):
    """
        Property 6: attach_blueprint_to_route registers all blueprint endpoints

        For any ``RestBlueprint`` subclass with registered endpoints,
        calling ``attach_blueprint_to_route`` and then ``startup()``
        shall result in the blueprint's ``register`` method being called
        with the application's Router.

        **Feature: webapp-lifecycle, Property 6: attach_blueprint_to_route registers all blueprint endpoints**
        **Validates: Requirements 3.1, 3.3**
    """
    patch = None

    try:
        reset_webapp_persona()

        app = establish_webapp_persona(
            name="testapp",
            logger_name="testapp",
            log_basename="testapp",
        )

        register_calls = []

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

        app.attach_blueprint_to_route(blueprint_cls)

        testbase.assert_equal(
            len(register_calls), 0,
            f"Expected register to not be called before startup, "
            f"got {len(register_calls)} calls"
        )

        patch = create_module_patch(webapp_module, "ManagedConfigRegistry")
        mock_cls = patch.activate()
        mock_registry = Mock()
        mock_registry.configure(recursive=True)
        mock_cls.configure(return_value=mock_registry)

        app.startup()

        testbase.assert_equal(
            len(register_calls), 1,
            f"Expected register to be called once during startup, "
            f"got {len(register_calls)} calls"
        )

        testbase.assert_true(
            register_calls[0] is app._router,
            f"Expected register to be called with the app's Router instance"
        )

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

@given(
    iteration=st.integers(0, 9999),
    constraints={"max_examples": 10},
)
def test_property_duplicate_blueprint_registration_raises_error(iteration):
    """
        Property 7: Duplicate blueprint registration raises error

        For any ``RestBlueprint`` subclass, calling
        ``attach_blueprint_to_route`` twice with the same class shall
        raise a ``BlueprintAlreadyRegisteredError`` on the second call.

        **Feature: webapp-lifecycle, Property 7: Duplicate blueprint registration raises error**
        **Validates: Requirements 3.2**
    """
    try:
        reset_webapp_persona()

        app = establish_webapp_persona(
            name="testapp",
            logger_name="testapp",
            log_basename="testapp",
        )

        blueprint_name = f"FakeBlueprint_{iteration}"

        blueprint_cls = type(
            blueprint_name,
            (),
            {
                "register": classmethod(lambda cls, router=None: None),
            },
        )

        app.attach_blueprint_to_route(blueprint_cls)

        caught_error = None

        try:
            app.attach_blueprint_to_route(blueprint_cls)
        except BlueprintAlreadyRegisteredError as err:
            caught_error = err

        testbase.assert_true(
            caught_error is not None,
            f"Expected BlueprintAlreadyRegisteredError when registering "
            f"'{blueprint_name}' twice, but no error was raised"
        )

        testbase.assert_true(
            caught_error.blueprint_cls is blueprint_cls,
            f"Expected BlueprintAlreadyRegisteredError.blueprint_cls to "
            f"reference the duplicate class '{blueprint_name}'"
        )

        error_message = str(caught_error)

        testbase.assert_true(
            blueprint_name in error_message,
            f"Expected error message to contain '{blueprint_name}', "
            f"got: '{error_message}'"
        )

    finally:
        reset_webapp_persona()

    return


if __name__ == "__main__":
    from ccai.testbase.entrypoints import generic_test_entrypoint
    generic_test_entrypoint()
