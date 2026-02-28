"""
    Property test for blueprint endpoint registration.

    This module verifies Property 1: Blueprint Endpoint Registration.

    For any authentication blueprint class with a configured base_path,
    when registered with a router, all default endpoints SHALL be
    registered at paths relative to the base_path.

    **Validates: Requirements 2.1, 3.1, 3.2, 3.3, 3.8, 4.1, 4.2, 4.3,
    4.4, 5.1, 5.2, 5.3, 6.1, 6.2, 6.3, 6.7, 7.2, 7.3, 7.4**
"""

__author__ = "Automation Mojo LLC"
__copyright__ = "Copyright 2025, Automation Mojo LLC"
__credits__ = []


import random

from automojo.webworks.authentication.blueprints.basic import BasicAuthBlueprint
from automojo.webworks.authentication.blueprints.bearer import BearerAuthBlueprint
from automojo.webworks.authentication.blueprints.apikey import APIKeyBlueprint
from automojo.webworks.authentication.blueprints.session import SessionAuthBlueprint
from automojo.webworks.authentication.blueprints.oauth2 import OAuth2Blueprint
from automojo.webworks.authentication.blueprints.oidc import OIDCBlueprint


# =============================================================================
# Expected endpoint definitions per blueprint (path, method)
# =============================================================================

BLUEPRINT_EXPECTED_ENDPOINTS = {
    "BasicAuthBlueprint": {
        "cls": BasicAuthBlueprint,
        "endpoints": {
            ("/auth/basic/login", "POST"),
            ("/auth/basic/logout", "POST"),
        }
    },
    "BearerAuthBlueprint": {
        "cls": BearerAuthBlueprint,
        "endpoints": {
            ("/auth/token", "POST"),
            ("/auth/token/refresh", "POST"),
            ("/auth/token/revoke", "POST"),
            ("/auth/token/introspect", "POST"),
        }
    },
    "APIKeyBlueprint": {
        "cls": APIKeyBlueprint,
        "endpoints": {
            ("/auth/keys", "POST"),
            ("/auth/keys", "GET"),
            ("/auth/keys/{key_id}", "GET"),
            ("/auth/keys/{key_id}", "DELETE"),
        }
    },
    "SessionAuthBlueprint": {
        "cls": SessionAuthBlueprint,
        "endpoints": {
            ("/auth/session/login", "POST"),
            ("/auth/session/logout", "POST"),
            ("/auth/session", "GET"),
        }
    },
    "OAuth2Blueprint": {
        "cls": OAuth2Blueprint,
        "endpoints": {
            ("/oauth/authorize", "GET"),
            ("/oauth/token", "POST"),
            ("/oauth/callback", "GET"),
            ("/oauth/revoke", "POST"),
        }
    },
    "OIDCBlueprint": {
        "cls": OIDCBlueprint,
        "endpoints": {
            ("/.well-known/openid-configuration", "GET"),
            ("/oidc/userinfo", "GET"),
            ("/.well-known/jwks.json", "GET"),
            ("/oidc/authorize", "GET"),
            ("/oidc/token", "POST"),
            ("/oidc/callback", "GET"),
            ("/oidc/revoke", "POST"),
        }
    },
}


# =============================================================================
# Test Helpers
# =============================================================================

class MockRouter:
    """
        A mock router that records add_endpoint calls.
    """

    def __init__(self):
        self.endpoints = []
        return

    def add_endpoint(self, descriptor):
        self.endpoints.append(descriptor)
        return


def _collect_registered_endpoints(blueprint_cls):
    """
        Register a blueprint with a mock router and return the set of
        (path, method) tuples that were registered.

        :param blueprint_cls: The blueprint class to register.

        :returns: A set of (path, method) tuples.
    """
    router = MockRouter()
    descriptors = blueprint_cls.register(router=router)

    registered = set()
    for descriptor in descriptors:
        path = descriptor.path
        if path is None and descriptor.leaf is not None:
            path = "/{}".format(descriptor.leaf)

        if path is not None:
            for method in descriptor.methods:
                registered.add((path, method))

    return registered


# =============================================================================
# Property Tests
# =============================================================================

def test_property_1_basic_auth_endpoint_registration():
    """
        Property 1: Blueprint Endpoint Registration - BasicAuthBlueprint.

        Verifies that BasicAuthBlueprint registers POST /login and
        POST /logout endpoints at paths relative to its base_path.

        **Validates: Requirements 2.1**
    """
    expected = BLUEPRINT_EXPECTED_ENDPOINTS["BasicAuthBlueprint"]["endpoints"]
    registered = _collect_registered_endpoints(BasicAuthBlueprint)

    for path, method in expected:
        if (path, method) not in registered:
            errmsg = (
                "BasicAuthBlueprint: Expected endpoint {} {} was not "
                "registered. Registered endpoints: {}".format(
                    method, path, sorted(registered)
                )
            )
            raise AssertionError(errmsg)

    return


def test_property_1_bearer_auth_endpoint_registration():
    """
        Property 1: Blueprint Endpoint Registration - BearerAuthBlueprint.

        Verifies that BearerAuthBlueprint registers token, refresh,
        revoke, and introspect endpoints at paths relative to its
        base_path.

        **Validates: Requirements 3.1, 3.2, 3.3, 3.8**
    """
    expected = BLUEPRINT_EXPECTED_ENDPOINTS["BearerAuthBlueprint"]["endpoints"]
    registered = _collect_registered_endpoints(BearerAuthBlueprint)

    for path, method in expected:
        if (path, method) not in registered:
            errmsg = (
                "BearerAuthBlueprint: Expected endpoint {} {} was not "
                "registered. Registered endpoints: {}".format(
                    method, path, sorted(registered)
                )
            )
            raise AssertionError(errmsg)

    return


def test_property_1_apikey_endpoint_registration():
    """
        Property 1: Blueprint Endpoint Registration - APIKeyBlueprint.

        Verifies that APIKeyBlueprint registers create, list, get, and
        revoke endpoints at paths relative to its base_path.

        **Validates: Requirements 4.1, 4.2, 4.3, 4.4**
    """
    expected = BLUEPRINT_EXPECTED_ENDPOINTS["APIKeyBlueprint"]["endpoints"]
    registered = _collect_registered_endpoints(APIKeyBlueprint)

    for path, method in expected:
        if (path, method) not in registered:
            errmsg = (
                "APIKeyBlueprint: Expected endpoint {} {} was not "
                "registered. Registered endpoints: {}".format(
                    method, path, sorted(registered)
                )
            )
            raise AssertionError(errmsg)

    return


def test_property_1_session_auth_endpoint_registration():
    """
        Property 1: Blueprint Endpoint Registration - SessionAuthBlueprint.

        Verifies that SessionAuthBlueprint registers login, logout, and
        info endpoints at paths relative to its base_path.

        **Validates: Requirements 5.1, 5.2, 5.3**
    """
    expected = BLUEPRINT_EXPECTED_ENDPOINTS["SessionAuthBlueprint"]["endpoints"]
    registered = _collect_registered_endpoints(SessionAuthBlueprint)

    for path, method in expected:
        if (path, method) not in registered:
            errmsg = (
                "SessionAuthBlueprint: Expected endpoint {} {} was not "
                "registered. Registered endpoints: {}".format(
                    method, path, sorted(registered)
                )
            )
            raise AssertionError(errmsg)

    return


def test_property_1_oauth2_endpoint_registration():
    """
        Property 1: Blueprint Endpoint Registration - OAuth2Blueprint.

        Verifies that OAuth2Blueprint registers authorize, token,
        callback, and revoke endpoints at paths relative to its
        base_path.

        **Validates: Requirements 6.1, 6.2, 6.3, 6.7**
    """
    expected = BLUEPRINT_EXPECTED_ENDPOINTS["OAuth2Blueprint"]["endpoints"]
    registered = _collect_registered_endpoints(OAuth2Blueprint)

    for path, method in expected:
        if (path, method) not in registered:
            errmsg = (
                "OAuth2Blueprint: Expected endpoint {} {} was not "
                "registered. Registered endpoints: {}".format(
                    method, path, sorted(registered)
                )
            )
            raise AssertionError(errmsg)

    return


def test_property_1_oidc_endpoint_registration():
    """
        Property 1: Blueprint Endpoint Registration - OIDCBlueprint.

        Verifies that OIDCBlueprint registers discovery, userinfo,
        jwks, and all inherited OAuth2 endpoints.

        **Validates: Requirements 7.2, 7.3, 7.4**
    """
    expected = BLUEPRINT_EXPECTED_ENDPOINTS["OIDCBlueprint"]["endpoints"]
    registered = _collect_registered_endpoints(OIDCBlueprint)

    for path, method in expected:
        if (path, method) not in registered:
            errmsg = (
                "OIDCBlueprint: Expected endpoint {} {} was not "
                "registered. Registered endpoints: {}".format(
                    method, path, sorted(registered)
                )
            )
            raise AssertionError(errmsg)

    return


def test_property_1_all_blueprints_register_correct_endpoints():
    """
        Property 1: Blueprint Endpoint Registration - All Blueprints.

        For any randomly selected authentication blueprint, when
        registered with a router, the exact set of expected endpoints
        SHALL be present among the registered descriptors.

        **Validates: Requirements 2.1, 3.1, 3.2, 3.3, 3.8, 4.1, 4.2,
        4.3, 4.4, 5.1, 5.2, 5.3, 6.1, 6.2, 6.3, 6.7, 7.2, 7.3, 7.4**
    """
    blueprint_names = list(BLUEPRINT_EXPECTED_ENDPOINTS.keys())
    num_iterations = 100

    for iteration in range(num_iterations):
        blueprint_name = random.choice(blueprint_names)
        expected_info = BLUEPRINT_EXPECTED_ENDPOINTS[blueprint_name]
        blueprint_cls = expected_info["cls"]
        expected_endpoints = expected_info["endpoints"]

        registered = _collect_registered_endpoints(blueprint_cls)

        for path, method in expected_endpoints:
            if (path, method) not in registered:
                errmsg = (
                    "Iteration {}: {} - Expected endpoint {} {} was "
                    "not registered. Registered: {}".format(
                        iteration, blueprint_name, method, path,
                        sorted(registered)
                    )
                )
                raise AssertionError(errmsg)

    return


def test_property_1_all_blueprints_paths_relative_to_base():
    """
        Property 1: Blueprint Endpoint Registration - Path Relativity.

        For any authentication blueprint, all registered endpoint paths
        SHALL be relative to the blueprint's base_path, except for
        absolute well-known paths used by OIDC.

        **Validates: Requirements 2.1, 3.1, 3.2, 3.3, 3.8, 4.1, 4.2,
        4.3, 4.4, 5.1, 5.2, 5.3, 6.1, 6.2, 6.3, 6.7, 7.2, 7.3, 7.4**
    """
    blueprint_names = list(BLUEPRINT_EXPECTED_ENDPOINTS.keys())
    num_iterations = 100

    for iteration in range(num_iterations):
        blueprint_name = random.choice(blueprint_names)
        expected_info = BLUEPRINT_EXPECTED_ENDPOINTS[blueprint_name]
        blueprint_cls = expected_info["cls"]

        base_path = blueprint_cls._get_base_path()

        router = MockRouter()
        descriptors = blueprint_cls.register(router=router)

        for descriptor in descriptors:
            desc_path = descriptor.path
            if desc_path is None and descriptor.leaf is not None:
                desc_path = "/{}".format(descriptor.leaf)

            if desc_path is None:
                continue

            # Well-known absolute paths are exempt from base_path check
            is_well_known = desc_path.startswith("/.well-known")

            if not is_well_known and base_path is not None:
                if not desc_path.startswith(base_path):
                    errmsg = (
                        "Iteration {}: {} - Endpoint path '{}' does "
                        "not start with base_path '{}'. All non-absolute "
                        "paths must be relative to the base_path.".format(
                            iteration, blueprint_name, desc_path, base_path
                        )
                    )
                    raise AssertionError(errmsg)

    return


def test_property_1_all_blueprints_descriptors_have_handlers():
    """
        Property 1: Blueprint Endpoint Registration - Handler Presence.

        For any authentication blueprint, every registered endpoint
        descriptor SHALL have a non-None handler callable.

        **Validates: Requirements 2.1, 3.1, 3.2, 3.3, 3.8, 4.1, 4.2,
        4.3, 4.4, 5.1, 5.2, 5.3, 6.1, 6.2, 6.3, 6.7, 7.2, 7.3, 7.4**
    """
    blueprint_names = list(BLUEPRINT_EXPECTED_ENDPOINTS.keys())
    num_iterations = 100

    for iteration in range(num_iterations):
        blueprint_name = random.choice(blueprint_names)
        expected_info = BLUEPRINT_EXPECTED_ENDPOINTS[blueprint_name]
        blueprint_cls = expected_info["cls"]

        router = MockRouter()
        descriptors = blueprint_cls.register(router=router)

        if len(descriptors) != len(router.endpoints):
            errmsg = (
                "Iteration {}: {} - register() returned {} descriptors "
                "but router received {} endpoints.".format(
                    iteration, blueprint_name,
                    len(descriptors), len(router.endpoints)
                )
            )
            raise AssertionError(errmsg)

        for descriptor in descriptors:
            if descriptor.handler is None:
                desc_path = descriptor.path or descriptor.leaf
                errmsg = (
                    "Iteration {}: {} - Descriptor for '{}' has a "
                    "None handler.".format(
                        iteration, blueprint_name, desc_path
                    )
                )
                raise AssertionError(errmsg)

            if not callable(descriptor.handler):
                desc_path = descriptor.path or descriptor.leaf
                errmsg = (
                    "Iteration {}: {} - Descriptor for '{}' has a "
                    "non-callable handler.".format(
                        iteration, blueprint_name, desc_path
                    )
                )
                raise AssertionError(errmsg)

    return
