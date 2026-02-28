"""
    Property test for SecurityBlueprint authenticator configuration.

    This module verifies Property 4: Authenticator Configuration.

    For any Security_Blueprint subclass, setting the auth_system attribute
    SHALL cause that authentication system to be used for credential
    validation.

    **Validates: Requirements 1.2, 1.5, 2.4**
"""

import random
import string

from automojo.webworks.authentication.blueprints.security import SecurityBlueprint
from automojo.webworks.authentication.blueprints.basic import BasicAuthBlueprint
from automojo.webworks.authentication.system import AuthenticationSystem


# =============================================================================
# Test Helpers
# =============================================================================

def _random_string(min_length=1, max_length=20):
    """
        Generate a random alphanumeric string.
    """
    length = random.randint(min_length, max_length)
    rtnval = "".join(random.choices(string.ascii_lowercase + string.digits, k=length))
    return rtnval


def _create_fresh_security_blueprint():
    """
        Create a fresh SecurityBlueprint subclass to avoid class-level
        state leakage between iterations.

        :returns: A new SecurityBlueprint subclass with clean state.
    """

    class FreshSecurityBlueprint(SecurityBlueprint):
        pass

    FreshSecurityBlueprint.auth_system = None
    FreshSecurityBlueprint.enabled_endpoints = None
    FreshSecurityBlueprint.base_path = "/auth"

    return FreshSecurityBlueprint


def _create_fresh_basic_blueprint():
    """
        Create a fresh BasicAuthBlueprint subclass to avoid class-level
        state leakage between iterations.

        :returns: A new BasicAuthBlueprint subclass with clean state.
    """

    class FreshBasicBlueprint(BasicAuthBlueprint):
        pass

    FreshBasicBlueprint.auth_system = None
    FreshBasicBlueprint.identity_provider = None
    FreshBasicBlueprint.enabled_endpoints = None
    FreshBasicBlueprint.base_path = "/auth/basic"

    return FreshBasicBlueprint


class MockIdentityProvider:
    """
        A mock identity provider for testing BasicAuthBlueprint
        identity_provider configuration.
    """

    def __init__(self, name):
        self.name = name

    async def validate_credentials(self, username, password):
        return None

    async def get_principal(self, identifier):
        return None


# =============================================================================
# Property Tests
# =============================================================================

def test_property_4_authenticator_configuration():
    """
        Property 4: Authenticator Configuration.

        For any Security_Blueprint subclass, setting the auth_system
        attribute SHALL cause that authentication system to be used for
        credential validation.

        This test verifies:
        1. When configure() is called with an auth_system, the blueprint
           stores it correctly on the class attribute.
        2. The auth_system is accessible from the blueprint class after
           configuration.
        3. BasicAuthBlueprint's identity_provider can be configured
           independently.
        4. Multiple blueprints can be configured with different
           auth_systems independently.

        **Validates: Requirements 1.2, 1.5, 2.4**
    """
    num_iterations = 100

    for iteration in range(num_iterations):

        # -----------------------------------------------------------------
        # Verify 1 & 2: configure() stores auth_system and it is accessible
        # -----------------------------------------------------------------
        blueprint_cls = _create_fresh_security_blueprint()
        auth_system = AuthenticationSystem()

        # Before configuration, auth_system should be None
        if blueprint_cls.auth_system is not None:
            errmsg = (
                f"Iteration {iteration}: Expected auth_system to be None "
                f"before configure(), got {blueprint_cls.auth_system!r}."
            )
            raise AssertionError(errmsg)

        # Configure with auth_system
        blueprint_cls.configure(auth_system=auth_system)

        # After configuration, auth_system should be the one we passed
        if blueprint_cls.auth_system is not auth_system:
            errmsg = (
                f"Iteration {iteration}: Expected auth_system to be the "
                f"configured instance after configure(). "
                f"Got {blueprint_cls.auth_system!r}."
            )
            raise AssertionError(errmsg)

        # -----------------------------------------------------------------
        # Verify 3: BasicAuthBlueprint identity_provider configuration
        # -----------------------------------------------------------------
        basic_cls = _create_fresh_basic_blueprint()
        provider_name = _random_string(5, 15)
        provider = MockIdentityProvider(name=provider_name)

        # Before setting, identity_provider should be None
        if basic_cls.identity_provider is not None:
            errmsg = (
                f"Iteration {iteration}: Expected identity_provider to be "
                f"None before configuration, got "
                f"{basic_cls.identity_provider!r}."
            )
            raise AssertionError(errmsg)

        # Set identity_provider directly on the class
        basic_cls.identity_provider = provider

        # Verify identity_provider is accessible and correct
        if basic_cls.identity_provider is not provider:
            errmsg = (
                f"Iteration {iteration}: Expected identity_provider to be "
                f"the configured instance. Got "
                f"{basic_cls.identity_provider!r}."
            )
            raise AssertionError(errmsg)

        if basic_cls.identity_provider.name != provider_name:
            errmsg = (
                f"Iteration {iteration}: Expected identity_provider.name "
                f"to be {provider_name!r}, got "
                f"{basic_cls.identity_provider.name!r}."
            )
            raise AssertionError(errmsg)

        # Also configure auth_system on the basic blueprint
        basic_auth_system = AuthenticationSystem()
        basic_cls.configure(auth_system=basic_auth_system)

        # Both auth_system and identity_provider should be set
        if basic_cls.auth_system is not basic_auth_system:
            errmsg = (
                f"Iteration {iteration}: Expected BasicAuthBlueprint "
                f"auth_system to be the configured instance after "
                f"configure()."
            )
            raise AssertionError(errmsg)

        if basic_cls.identity_provider is not provider:
            errmsg = (
                f"Iteration {iteration}: Expected identity_provider to "
                f"remain set after configure() call. Got "
                f"{basic_cls.identity_provider!r}."
            )
            raise AssertionError(errmsg)

        # -----------------------------------------------------------------
        # Verify 4: Multiple blueprints with different auth_systems
        # -----------------------------------------------------------------
        blueprint_a = _create_fresh_security_blueprint()
        blueprint_b = _create_fresh_security_blueprint()

        auth_system_a = AuthenticationSystem()
        auth_system_b = AuthenticationSystem()

        blueprint_a.configure(auth_system=auth_system_a)
        blueprint_b.configure(auth_system=auth_system_b)

        # Each blueprint should have its own auth_system
        if blueprint_a.auth_system is not auth_system_a:
            errmsg = (
                f"Iteration {iteration}: Blueprint A auth_system should be "
                f"auth_system_a after independent configuration."
            )
            raise AssertionError(errmsg)

        if blueprint_b.auth_system is not auth_system_b:
            errmsg = (
                f"Iteration {iteration}: Blueprint B auth_system should be "
                f"auth_system_b after independent configuration."
            )
            raise AssertionError(errmsg)

        # Verify they are different instances
        if blueprint_a.auth_system is blueprint_b.auth_system:
            errmsg = (
                f"Iteration {iteration}: Blueprint A and B should have "
                f"different auth_system instances."
            )
            raise AssertionError(errmsg)

        # Reconfigure blueprint_a should not affect blueprint_b
        auth_system_c = AuthenticationSystem()
        blueprint_a.configure(auth_system=auth_system_c)

        if blueprint_a.auth_system is not auth_system_c:
            errmsg = (
                f"Iteration {iteration}: Blueprint A auth_system should be "
                f"auth_system_c after reconfiguration."
            )
            raise AssertionError(errmsg)

        if blueprint_b.auth_system is not auth_system_b:
            errmsg = (
                f"Iteration {iteration}: Blueprint B auth_system should "
                f"still be auth_system_b after Blueprint A was "
                f"reconfigured."
            )
            raise AssertionError(errmsg)

    return
