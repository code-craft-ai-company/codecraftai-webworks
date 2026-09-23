"""
    Property test for access policy application.

    This module verifies Property 22: Access Policy Application.

    For any Security_Blueprint with configured access_policy, that policy
    SHALL be applied to all blueprint endpoints.

    **Validates: Requirements 9.4**
"""

import random

from ccai.webworks.endpoints.accesspolicy import AccessPolicy
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
        Remove the access_policy attribute from a blueprint class so
        that tests do not leak state between each other.
    """
    if hasattr(blueprint_cls, "access_policy"):
        delattr(blueprint_cls, "access_policy")
    return


def _generate_random_policy():
    """
        Generate a random AccessPolicy with varying roles, scopes,
        and require_auth settings.
    """
    possible_roles = ["admin", "editor", "viewer", "operator", "auditor"]
    possible_scopes = ["read", "write", "delete", "manage", "audit"]

    num_roles = random.randint(0, 3)
    num_scopes = random.randint(0, 3)

    roles = random.sample(possible_roles, num_roles)
    scopes = random.sample(possible_scopes, num_scopes)
    require_auth = random.choice([True, False])

    policy = AccessPolicy(
        roles=roles,
        scopes=scopes,
        require_auth=require_auth
    )
    return policy



# =============================================================================
# Property Tests
# =============================================================================

def test_property_22_set_access_policy_propagates_to_descriptors():
    """
        Property 22: Access Policy Application - set_access_policy.

        When set_access_policy is called on a blueprint, the policy SHALL
        be propagated to all endpoint descriptors built by register().

        **Validates: Requirements 9.4**
    """
    for blueprint_cls in ALL_BLUEPRINT_CLASSES:
        policy = AccessPolicy(
            roles=["admin", "editor"],
            scopes=["read", "write"],
            require_auth=True
        )

        try:
            blueprint_cls.set_access_policy(policy)
            descriptors = blueprint_cls.register()

            if len(descriptors) == 0:
                errmsg = (
                    f"{blueprint_cls.__name__}: register() returned no "
                    f"descriptors. Expected at least one endpoint."
                )
                raise AssertionError(errmsg)

            for descriptor in descriptors:
                ep_policy = descriptor.constraints.access_policy

                if ep_policy is None:
                    errmsg = (
                        f"{blueprint_cls.__name__}: Descriptor for "
                        f"{descriptor.path} has no access_policy after "
                        f"set_access_policy was called."
                    )
                    raise AssertionError(errmsg)

                if ep_policy.roles != policy.roles:
                    errmsg = (
                        f"{blueprint_cls.__name__}: Descriptor for "
                        f"{descriptor.path} has roles {ep_policy.roles}, "
                        f"expected {policy.roles}."
                    )
                    raise AssertionError(errmsg)

                if ep_policy.scopes != policy.scopes:
                    errmsg = (
                        f"{blueprint_cls.__name__}: Descriptor for "
                        f"{descriptor.path} has scopes {ep_policy.scopes}, "
                        f"expected {policy.scopes}."
                    )
                    raise AssertionError(errmsg)

                if ep_policy.require_auth != policy.require_auth:
                    errmsg = (
                        f"{blueprint_cls.__name__}: Descriptor for "
                        f"{descriptor.path} has require_auth "
                        f"{ep_policy.require_auth}, expected "
                        f"{policy.require_auth}."
                    )
                    raise AssertionError(errmsg)
        finally:
            _cleanup_blueprint(blueprint_cls)

    return


def test_property_22_configure_access_policy_propagates_to_descriptors():
    """
        Property 22: Access Policy Application - configure with access_policy.

        When configure() is called with an access_policy parameter, the
        policy SHALL be propagated to all endpoint descriptors.

        **Validates: Requirements 9.4**
    """
    for blueprint_cls in ALL_BLUEPRINT_CLASSES:
        policy = AccessPolicy(
            roles=["viewer"],
            scopes=["read"],
            require_auth=False
        )

        try:
            blueprint_cls.configure(
                auth_system=None,
                access_policy=policy
            )
            descriptors = blueprint_cls.register()

            if len(descriptors) == 0:
                errmsg = (
                    f"{blueprint_cls.__name__}: register() returned no "
                    f"descriptors after configure()."
                )
                raise AssertionError(errmsg)

            for descriptor in descriptors:
                ep_policy = descriptor.constraints.access_policy

                if ep_policy is None:
                    errmsg = (
                        f"{blueprint_cls.__name__}: Descriptor for "
                        f"{descriptor.path} has no access_policy after "
                        f"configure(access_policy=...) was called."
                    )
                    raise AssertionError(errmsg)

                if ep_policy.require_auth != policy.require_auth:
                    errmsg = (
                        f"{blueprint_cls.__name__}: Descriptor for "
                        f"{descriptor.path} has require_auth "
                        f"{ep_policy.require_auth}, expected "
                        f"{policy.require_auth}."
                    )
                    raise AssertionError(errmsg)
        finally:
            _cleanup_blueprint(blueprint_cls)
            blueprint_cls.auth_system = None

    return


def test_property_22_random_policy_propagation():
    """
        Property 22: Access Policy Application - Random policies.

        For any randomly generated AccessPolicy applied to any randomly
        selected blueprint, the policy SHALL be propagated to all
        endpoint descriptors.

        **Validates: Requirements 9.4**
    """
    num_iterations = 100

    for iteration in range(num_iterations):
        blueprint_cls = random.choice(ALL_BLUEPRINT_CLASSES)
        policy = _generate_random_policy()

        try:
            blueprint_cls.set_access_policy(policy)
            descriptors = blueprint_cls.register()

            for descriptor in descriptors:
                ep_policy = descriptor.constraints.access_policy

                if ep_policy is None:
                    errmsg = (
                        f"Iteration {iteration}: "
                        f"{blueprint_cls.__name__} descriptor for "
                        f"{descriptor.path} has no access_policy. "
                        f"Policy was {policy}."
                    )
                    raise AssertionError(errmsg)

                if set(ep_policy.roles) != set(policy.roles):
                    errmsg = (
                        f"Iteration {iteration}: "
                        f"{blueprint_cls.__name__} descriptor for "
                        f"{descriptor.path} has roles {ep_policy.roles}, "
                        f"expected {policy.roles}."
                    )
                    raise AssertionError(errmsg)

                if set(ep_policy.scopes) != set(policy.scopes):
                    errmsg = (
                        f"Iteration {iteration}: "
                        f"{blueprint_cls.__name__} descriptor for "
                        f"{descriptor.path} has scopes {ep_policy.scopes}, "
                        f"expected {policy.scopes}."
                    )
                    raise AssertionError(errmsg)

                if ep_policy.require_auth != policy.require_auth:
                    errmsg = (
                        f"Iteration {iteration}: "
                        f"{blueprint_cls.__name__} descriptor for "
                        f"{descriptor.path} has require_auth "
                        f"{ep_policy.require_auth}, expected "
                        f"{policy.require_auth}."
                    )
                    raise AssertionError(errmsg)
        finally:
            _cleanup_blueprint(blueprint_cls)

    return
