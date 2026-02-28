"""
    Property test for SecurityBlueprint custom endpoint addition.

    This module verifies Property 20: Custom Endpoint Addition.

    For any SecurityBlueprint subclass with additional endpoints defined
    via attach_at, those endpoints SHALL be registered alongside default
    endpoints.

    **Validates: Requirements 8.3**
"""

import random
import string

from automojo.webworks.authentication.blueprints.security import SecurityBlueprint
from automojo.webworks.endpoints.registry import EndpointRegistry
from automojo.webworks.endpoints.doc import Doc


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


def _random_path_segment():
    """
        Generate a random URL path segment.

        :returns: A string suitable for use as a URL path segment.
    """
    segment = _random_string(3, 10)
    return segment


# =============================================================================
# Property Tests
# =============================================================================

def test_property_20_custom_endpoint_addition():
    """
        Property 20: Custom Endpoint Addition.

        For any SecurityBlueprint subclass with additional endpoints
        defined via attach_at, those endpoints SHALL be registered
        alongside default endpoints.

        This test verifies:
        1. A subclass can use attach_at to add custom endpoints.
        2. Custom endpoints are registered in the EndpointRegistry.
        3. Custom endpoints have paths computed relative to the
           blueprint's base_path.
        4. Both default and custom endpoints coexist in the registry.
        5. Custom endpoints with different HTTP methods are registered
           correctly.

        **Validates: Requirements 8.3**
    """
    num_iterations = 100

    for iteration in range(num_iterations):
        # Clear the registry before each iteration to avoid conflicts
        EndpointRegistry.clear()

        # Generate random base path and custom leaf names
        base_segment = _random_path_segment()
        base_path = f"/test/{base_segment}"
        default_leaf = "default_" + _random_string(3, 8)
        custom_leaf = "custom_" + _random_string(3, 8)

        # Choose random HTTP method for the custom endpoint
        custom_method = random.choice(["GET", "POST", "PUT", "DELETE"])

        # Create a blueprint subclass with a default endpoint and a
        # custom endpoint added via attach_at

        class TestBlueprint(SecurityBlueprint):
            pass

        TestBlueprint.base_path = base_path
        TestBlueprint.tags = ["Test"]
        TestBlueprint.enabled_endpoints = None

        # Register a default endpoint using the create decorator
        @TestBlueprint.create(
            leaf=default_leaf,
            doc=Doc(
                summary="Default endpoint",
                description="A default endpoint for testing.",
            ),
            on_conflict="replace",
        )
        def default_handler(cls, request):
            return {"status": 200, "body": {"type": "default"}}

        # Add the handler as a class attribute so register() can find it
        TestBlueprint.default_handler = default_handler

        # Register a custom endpoint using attach_at
        @TestBlueprint.attach_at(
            leaf=custom_leaf,
            methods=[custom_method],
            doc=Doc(
                summary="Custom endpoint",
                description="A custom endpoint added via attach_at.",
            ),
            on_conflict="replace",
        )
        def custom_handler(cls, request):
            return {"status": 200, "body": {"type": "custom"}}

        # Add the handler as a class attribute so register() can find it
        TestBlueprint.custom_handler = custom_handler

        # Register the blueprint endpoints with the global registry
        TestBlueprint.register_with_registry(on_conflict="replace")

        # Collect all registered descriptors
        all_descriptors = EndpointRegistry.collect()

        # --- Verify default endpoint is registered ---

        expected_default_path = f"{base_path}/{default_leaf}"
        default_found = False

        for desc in all_descriptors:
            desc_path = desc.path
            if desc_path is not None and desc_path == expected_default_path:
                default_found = True
                break

        if not default_found:
            errmsg = (
                f"Iteration {iteration}: Default endpoint at "
                f"'{expected_default_path}' was not found in the "
                f"registry. Registered paths: "
                f"{[d.path for d in all_descriptors]}."
            )
            raise AssertionError(errmsg)

        # --- Verify custom endpoint is registered ---

        expected_custom_path = f"{base_path}/{custom_leaf}"
        custom_found = False
        custom_descriptor = None

        for desc in all_descriptors:
            desc_path = desc.path
            if desc_path is not None and desc_path == expected_custom_path:
                custom_found = True
                custom_descriptor = desc
                break

        if not custom_found:
            errmsg = (
                f"Iteration {iteration}: Custom endpoint at "
                f"'{expected_custom_path}' was not found in the "
                f"registry. Registered paths: "
                f"{[d.path for d in all_descriptors]}."
            )
            raise AssertionError(errmsg)

        # --- Verify custom endpoint has correct HTTP method ---

        if custom_descriptor is not None:
            if custom_method not in custom_descriptor.methods:
                errmsg = (
                    f"Iteration {iteration}: Custom endpoint at "
                    f"'{expected_custom_path}' should have method "
                    f"'{custom_method}', got {custom_descriptor.methods}."
                )
                raise AssertionError(errmsg)

        # --- Verify custom endpoint path starts with base_path ---

        if not expected_custom_path.startswith(base_path):
            errmsg = (
                f"Iteration {iteration}: Custom endpoint path "
                f"'{expected_custom_path}' does not start with "
                f"base_path '{base_path}'."
            )
            raise AssertionError(errmsg)

        # --- Verify both endpoints coexist ---

        blueprint_descriptors = TestBlueprint._collect_blueprint_descriptors(
            all_descriptors
        )

        found_default = False
        found_custom = False

        for desc in blueprint_descriptors:
            if desc.path == expected_default_path:
                found_default = True
            if desc.path == expected_custom_path:
                found_custom = True

        if not found_default:
            errmsg = (
                f"Iteration {iteration}: Default endpoint not found "
                f"among blueprint descriptors."
            )
            raise AssertionError(errmsg)

        if not found_custom:
            errmsg = (
                f"Iteration {iteration}: Custom endpoint not found "
                f"among blueprint descriptors."
            )
            raise AssertionError(errmsg)

        # --- Verify custom endpoint handler is the correct function ---

        if custom_descriptor.handler is not custom_handler:
            errmsg = (
                f"Iteration {iteration}: Custom endpoint handler "
                f"does not match the registered function."
            )
            raise AssertionError(errmsg)

    # Final cleanup
    EndpointRegistry.clear()

    return
