"""
    Property test for blueprint router integration.

    This module verifies Property 21: Blueprint Router Integration.

    For any Security_Blueprint registered with a Router, all enabled
    endpoints SHALL be accessible via the router's request handling.

    **Validates: Requirements 9.1, 9.2, 9.6**
"""

import random

from ccai.webworks.endpoints.registry import EndpointRegistry
from ccai.webworks.routing.router import Router
from ccai.webworks.routing.request import Request
from ccai.webworks.authentication.blueprints.basic import BasicAuthBlueprint
from ccai.webworks.authentication.blueprints.bearer import BearerAuthBlueprint
from ccai.webworks.authentication.blueprints.apikey import APIKeyBlueprint
from ccai.webworks.authentication.blueprints.session import SessionAuthBlueprint
from ccai.webworks.authentication.blueprints.oauth2 import OAuth2Blueprint
from ccai.webworks.authentication.blueprints.oidc import OIDCBlueprint


# =============================================================================
# Registry setup
# =============================================================================


# All :class:`SecurityBlueprint` subclasses whose endpoints participate
# in Property 21's router-integration assertions. The registration order
# is deterministic so any conflict diagnostic mentions handlers in a
# stable order.
_SECURITY_BLUEPRINT_CLASSES = [
    BasicAuthBlueprint,
    BearerAuthBlueprint,
    APIKeyBlueprint,
    SessionAuthBlueprint,
    OAuth2Blueprint,
    OIDCBlueprint,
]


def _populated_registry() -> EndpointRegistry:
    """
        Build a fresh :class:`EndpointRegistry` populated with the six
        security blueprints. Every test in this module calls this at
        the top so its setup is explicit and its state is its own.

        :class:`SecurityBlueprint` subclasses deliberately defer
        registration to an explicit :meth:`register` call (their
        decorator overrides only attach metadata to the handler — see
        ``security.py`` for the rationale: sibling blueprints share
        leaf names like ``"login"``, so eager class-definition-time
        registration would raise :class:`EndpointConflictError`).

        Property 21's assertions exercise the *populated* registry, so
        each test needs the six blueprint classes registered before it
        runs. A registry is an ordinary instance-scoped object, so a new
        one per test carries no pollution from earlier tests and needs
        no teardown. Registration uses ``on_conflict="replace"`` so a
        re-run within the same process is idempotent.

        :returns: A registry holding the descriptors of every blueprint
                  in :data:`_SECURITY_BLUEPRINT_CLASSES`.
    """
    registry = EndpointRegistry()
    for blueprint_cls in _SECURITY_BLUEPRINT_CLASSES:
        blueprint_cls.register_with_registry(registry=registry, on_conflict="replace")

    return registry


# =============================================================================
# Test Helpers
# =============================================================================

def _create_request(path, method="GET"):
    """
        Create a Request object for testing router matching.
    """
    request = Request(method=method, path=path)
    return request


def _build_router_from_registry(registry: EndpointRegistry):
    """
        Build a Router and load all endpoints from the given registry.

        :param registry: The populated registry to load routes from.
    """
    router = Router(strict_slashes=False, case_sensitive=True)
    router.load_from_registry(registry)
    return router


def _get_descriptor_path(descriptor):
    """
        Extract the path from a descriptor.
    """
    if descriptor.path is not None:
        return descriptor.path
    elif descriptor.leaf is not None:
        return "/" + descriptor.leaf
    return None


# =============================================================================
# Property Tests
# =============================================================================

def test_property_21_registry_descriptors_have_handlers():
    """
        Property 21: Blueprint Router Integration - Registry Descriptors.

        Verifies that all descriptors in the EndpointRegistry have valid
        handlers and paths.

        **Validates: Requirements 9.1**
    """
    registry = _populated_registry()
    descriptors = registry.collect()

    if len(descriptors) == 0:
        errmsg = "EndpointRegistry has no descriptors registered."
        raise AssertionError(errmsg)

    for descriptor in descriptors:
        if descriptor.handler is None:
            errmsg = (
                f"Descriptor with path={descriptor.path!r} "
                f"leaf={descriptor.leaf!r} has no handler."
            )
            raise AssertionError(errmsg)

        if descriptor.path is None and descriptor.leaf is None:
            errmsg = (
                f"Descriptor for handler {descriptor.handler.__name__} "
                f"has neither path nor leaf."
            )
            raise AssertionError(errmsg)

    return


def test_property_21_router_loads_all_registry_endpoints():
    """
        Property 21: Blueprint Router Integration - Router Loading.

        Verifies that a Router can load all endpoints from the
        EndpointRegistry without errors.

        **Validates: Requirements 9.1, 9.2**
    """
    registry = _populated_registry()
    router = _build_router_from_registry(registry)

    # The router should have loaded routes
    route_count = len(router._routes)

    if route_count == 0:
        errmsg = "Router loaded 0 routes from the registry."
        raise AssertionError(errmsg)

    return


def test_property_21_router_matches_registered_endpoints():
    """
        Property 21: Blueprint Router Integration - Route Matching.

        Verifies that all endpoints loaded from the registry are
        matchable via the router's match method.

        **Validates: Requirements 9.1, 9.2, 9.6**
    """
    registry = _populated_registry()
    router = _build_router_from_registry(registry)

    descriptors = registry.collect()

    for descriptor in descriptors:
        desc_path = _get_descriptor_path(descriptor)
        if desc_path is None:
            continue

        # Substitute path parameters with test values
        test_path = desc_path.replace("{key_id}", "test-key-123")

        for method in descriptor.methods:
            request = _create_request(test_path, method)
            match = router.match(request)

            if match is None:
                errmsg = (
                    f"Router did not match {method} {test_path} "
                    f"(registered path: {desc_path}, "
                    f"handler: {descriptor.handler.__name__})."
                )
                raise AssertionError(errmsg)

            if match.handler is None:
                errmsg = (
                    f"Router matched {method} {test_path} but "
                    f"handler is None."
                )
                raise AssertionError(errmsg)

    return


def test_property_21_blueprint_register_adds_to_router():
    """
        Property 21: Blueprint Router Integration - Blueprint Register.

        Verifies that calling register(router=router) on a blueprint
        adds its descriptors to the router and they are matchable.

        **Validates: Requirements 9.1, 9.2, 9.6**
    """
    blueprint_classes = [
        BasicAuthBlueprint,
        BearerAuthBlueprint,
        APIKeyBlueprint,
        SessionAuthBlueprint,
        OAuth2Blueprint,
        OIDCBlueprint,
    ]

    num_iterations = 100

    for iteration in range(num_iterations):
        blueprint_cls = random.choice(blueprint_classes)

        router = Router(strict_slashes=False, case_sensitive=True)
        descriptors = blueprint_cls.register(router=router)

        # Every descriptor returned should be matchable in the router
        for descriptor in descriptors:
            desc_path = _get_descriptor_path(descriptor)
            if desc_path is None:
                continue

            test_path = desc_path.replace("{key_id}", "test-key-abc")

            for method in descriptor.methods:
                request = _create_request(test_path, method)
                match = router.match(request)

                if match is None:
                    errmsg = (
                        f"Iteration {iteration}: {blueprint_cls.__name__} "
                        f"- Router did not match {method} {test_path} "
                        f"after register()."
                    )
                    raise AssertionError(errmsg)

    return


def test_property_21_unregistered_paths_do_not_match():
    """
        Property 21: Blueprint Router Integration - Negative Test.

        Verifies that paths NOT registered by any blueprint do not
        match in the router.

        **Validates: Requirements 9.6**
    """
    registry = _populated_registry()
    router = _build_router_from_registry(registry)

    num_iterations = 100

    for iteration in range(num_iterations):
        # Generate a random path that should not be registered
        random_segment = "".join(
            random.choices("abcdefghijklmnopqrstuvwxyz", k=10)
        )
        fake_path = f"/nonexistent/{random_segment}/endpoint"

        request = _create_request(fake_path, "GET")
        match = router.match(request)

        if match is not None:
            errmsg = (
                f"Iteration {iteration}: Router unexpectedly matched "
                f"GET {fake_path}."
            )
            raise AssertionError(errmsg)

    return


def test_property_21_router_preserves_handler_reference():
    """
        Property 21: Blueprint Router Integration - Handler Preservation.

        Verifies that the handler returned by router.match() is the
        same handler that was registered in the descriptor.

        **Validates: Requirements 9.2, 9.6**
    """
    registry = _populated_registry()
    router = _build_router_from_registry(registry)

    descriptors = registry.collect()

    for descriptor in descriptors:
        desc_path = _get_descriptor_path(descriptor)
        if desc_path is None:
            continue

        test_path = desc_path.replace("{key_id}", "test-key-xyz")

        for method in descriptor.methods:
            request = _create_request(test_path, method)
            match = router.match(request)

            if match is None:
                continue

            if match.handler is not descriptor.handler:
                errmsg = (
                    f"Router returned different handler for "
                    f"{method} {test_path}. Expected "
                    f"{descriptor.handler.__name__}, got "
                    f"{match.handler.__name__}."
                )
                raise AssertionError(errmsg)

    return
