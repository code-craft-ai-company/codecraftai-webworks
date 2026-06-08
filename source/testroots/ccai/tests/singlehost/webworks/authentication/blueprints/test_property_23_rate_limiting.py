"""
    Property test for rate limiting application.

    This module verifies Property 23: Rate Limiting Application.

    For any Security_Blueprint with configured rate_limit, the rate limit
    SHALL be applied to all endpoint descriptors.

    **Validates: Requirements 9.5, 10.4**
"""

import random

from ccai.webworks.endpoints.ratelimit import RateLimit
from ccai.webworks.authentication.blueprints.security import SecurityBlueprint
from ccai.webworks.authentication.blueprints.basic import BasicAuthBlueprint
from ccai.webworks.authentication.blueprints.bearer import BearerAuthBlueprint
from ccai.webworks.authentication.blueprints.apikey import APIKeyBlueprint
from ccai.webworks.authentication.blueprints.session import SessionAuthBlueprint
from ccai.webworks.authentication.blueprints.oauth2 import OAuth2Blueprint
from ccai.webworks.authentication.blueprints.oidc import OIDCBlueprint


# =============================================================================
# Blueprint classes under test
# =============================================================================

ALL_BLUEPRINT_CLASSES = [
    BasicAuthBlueprint,
    BearerAuthBlueprint,
    APIKeyBlueprint,
    SessionAuthBlueprint,
    OAuth2Blueprint,
    OIDCBlueprint,
]


# =============================================================================
# Test Helpers
# =============================================================================

def _cleanup_blueprint(blueprint_cls):
    """
        Remove the rate_limit attribute from a blueprint class so
        that tests do not leak state between each other.
    """
    if hasattr(blueprint_cls, "rate_limit"):
        delattr(blueprint_cls, "rate_limit")
    return


def _generate_random_rate_limit():
    """
        Generate a random RateLimit with varying requests and window
        values.
    """
    requests = random.randint(1, 1000)
    window = random.randint(1, 3600)

    rate_limit = RateLimit(
        requests=requests,
        window=window
    )
    return rate_limit


# =============================================================================
# Property Tests
# =============================================================================

def test_property_23_set_rate_limit_propagates_to_descriptors():
    """
        Property 23: Rate Limiting Application - set_rate_limit.

        When set_rate_limit is called on a blueprint, the rate limit SHALL
        be propagated to all endpoint descriptors built by register().

        **Validates: Requirements 9.5, 10.4**
    """
    for blueprint_cls in ALL_BLUEPRINT_CLASSES:
        rate_limit = RateLimit(requests=100, window=60)

        try:
            blueprint_cls.set_rate_limit(rate_limit)
            descriptors = blueprint_cls.register()

            if len(descriptors) == 0:
                errmsg = (
                    f"{blueprint_cls.__name__}: register() returned no "
                    f"descriptors. Expected at least one endpoint."
                )
                raise AssertionError(errmsg)

            for descriptor in descriptors:
                ep_rate = descriptor.constraints.rate_limit

                if ep_rate is None:
                    errmsg = (
                        f"{blueprint_cls.__name__}: Descriptor for "
                        f"{descriptor.path} has no rate_limit after "
                        f"set_rate_limit was called."
                    )
                    raise AssertionError(errmsg)

                if ep_rate.requests != rate_limit.requests:
                    errmsg = (
                        f"{blueprint_cls.__name__}: Descriptor for "
                        f"{descriptor.path} has requests={ep_rate.requests}, "
                        f"expected {rate_limit.requests}."
                    )
                    raise AssertionError(errmsg)

                if ep_rate.window != rate_limit.window:
                    errmsg = (
                        f"{blueprint_cls.__name__}: Descriptor for "
                        f"{descriptor.path} has window={ep_rate.window}, "
                        f"expected {rate_limit.window}."
                    )
                    raise AssertionError(errmsg)
        finally:
            _cleanup_blueprint(blueprint_cls)

    return


def test_property_23_configure_rate_limit_propagates_to_descriptors():
    """
        Property 23: Rate Limiting Application - configure with rate_limit.

        When configure() is called with a rate_limit parameter, the rate
        limit SHALL be propagated to all endpoint descriptors.

        **Validates: Requirements 9.5, 10.4**
    """
    for blueprint_cls in ALL_BLUEPRINT_CLASSES:
        rate_limit = RateLimit(requests=50, window=30)

        try:
            blueprint_cls.configure(
                auth_system=None,
                rate_limit=rate_limit
            )
            descriptors = blueprint_cls.register()

            if len(descriptors) == 0:
                errmsg = (
                    f"{blueprint_cls.__name__}: register() returned no "
                    f"descriptors after configure()."
                )
                raise AssertionError(errmsg)

            for descriptor in descriptors:
                ep_rate = descriptor.constraints.rate_limit

                if ep_rate is None:
                    errmsg = (
                        f"{blueprint_cls.__name__}: Descriptor for "
                        f"{descriptor.path} has no rate_limit after "
                        f"configure(rate_limit=...) was called."
                    )
                    raise AssertionError(errmsg)

                if ep_rate.requests != rate_limit.requests:
                    errmsg = (
                        f"{blueprint_cls.__name__}: Descriptor for "
                        f"{descriptor.path} has requests={ep_rate.requests}, "
                        f"expected {rate_limit.requests}."
                    )
                    raise AssertionError(errmsg)

                if ep_rate.window != rate_limit.window:
                    errmsg = (
                        f"{blueprint_cls.__name__}: Descriptor for "
                        f"{descriptor.path} has window={ep_rate.window}, "
                        f"expected {rate_limit.window}."
                    )
                    raise AssertionError(errmsg)
        finally:
            _cleanup_blueprint(blueprint_cls)
            blueprint_cls.auth_system = None

    return


def test_property_23_random_rate_limit_propagation():
    """
        Property 23: Rate Limiting Application - Random rate limits.

        For any randomly generated RateLimit applied to any randomly
        selected blueprint, the rate limit SHALL be propagated to all
        endpoint descriptors.

        **Validates: Requirements 9.5, 10.4**
    """
    num_iterations = 100

    for iteration in range(num_iterations):
        blueprint_cls = random.choice(ALL_BLUEPRINT_CLASSES)
        rate_limit = _generate_random_rate_limit()

        try:
            blueprint_cls.set_rate_limit(rate_limit)
            descriptors = blueprint_cls.register()

            for descriptor in descriptors:
                ep_rate = descriptor.constraints.rate_limit

                if ep_rate is None:
                    errmsg = (
                        f"Iteration {iteration}: "
                        f"{blueprint_cls.__name__} descriptor for "
                        f"{descriptor.path} has no rate_limit. "
                        f"RateLimit was {rate_limit}."
                    )
                    raise AssertionError(errmsg)

                if ep_rate.requests != rate_limit.requests:
                    errmsg = (
                        f"Iteration {iteration}: "
                        f"{blueprint_cls.__name__} descriptor for "
                        f"{descriptor.path} has requests={ep_rate.requests}, "
                        f"expected {rate_limit.requests}."
                    )
                    raise AssertionError(errmsg)

                if ep_rate.window != rate_limit.window:
                    errmsg = (
                        f"Iteration {iteration}: "
                        f"{blueprint_cls.__name__} descriptor for "
                        f"{descriptor.path} has window={ep_rate.window}, "
                        f"expected {rate_limit.window}."
                    )
                    raise AssertionError(errmsg)
        finally:
            _cleanup_blueprint(blueprint_cls)

    return
