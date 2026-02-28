"""
    Property test for SecurityBlueprint path customization.

    This module verifies Property 7: Path Customization.

    For any SecurityBlueprint subclass with a custom base_path, all
    registered endpoints SHALL have paths prefixed with that base_path.

    **Validates: Requirements 2.5, 8.2**
"""

import random
import string

from automojo.webworks.authentication.blueprints.security import SecurityBlueprint
from automojo.webworks.endpoints.registry import EndpointRegistry


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
    segment = _random_string(3, 12)
    return segment


def _random_base_path():
    """
        Generate a random base path with 1-3 segments.

        :returns: A string like "/api/v1/auth" with random segments.
    """
    num_segments = random.randint(1, 3)
    segments = [_random_path_segment() for _ in range(num_segments)]
    base_path = "/" + "/".join(segments)
    return base_path


# =============================================================================
# Property Tests
# =============================================================================

def test_property_7_path_customization():
    """
        Property 7: Path Customization.

        For any SecurityBlueprint subclass with a custom base_path, all
        registered endpoints SHALL have paths prefixed with that base_path.

        This test verifies:
        1. When a blueprint has a custom base_path, _compute_full_path
           produces paths that start with that base_path.
        2. When base_path is changed via configure(), subsequent path
           computations use the new base_path.
        3. Leaf-based endpoints are correctly prefixed.
        4. Path-based endpoints are correctly prefixed.
        5. Trailing slashes on base_path are handled correctly.

        **Validates: Requirements 2.5, 8.2**
    """
    num_iterations = 100

    for iteration in range(num_iterations):
        base_path = _random_base_path()
        leaf_name = _random_path_segment()
        sub_path = _random_path_segment()

        # --- Test 1: Subclass with custom base_path ---

        class CustomPathBlueprint(SecurityBlueprint):
            pass

        CustomPathBlueprint.base_path = base_path

        # Verify _get_base_path returns the custom path
        resolved_base = CustomPathBlueprint._get_base_path()
        expected_base = base_path.rstrip("/")

        if resolved_base != expected_base:
            errmsg = (
                f"Iteration {iteration}: _get_base_path returned "
                f"'{resolved_base}', expected '{expected_base}'."
            )
            raise AssertionError(errmsg)

        # --- Test 2: Leaf-based endpoint path computation ---

        computed_leaf_path = CustomPathBlueprint._compute_full_path(
            leaf=leaf_name, path=None
        )

        expected_leaf_path = f"{expected_base}/{leaf_name}"

        if computed_leaf_path != expected_leaf_path:
            errmsg = (
                f"Iteration {iteration}: Leaf-based path computation "
                f"failed. Expected '{expected_leaf_path}', got "
                f"'{computed_leaf_path}'."
            )
            raise AssertionError(errmsg)

        if not computed_leaf_path.startswith(expected_base):
            errmsg = (
                f"Iteration {iteration}: Leaf-based path "
                f"'{computed_leaf_path}' does not start with base "
                f"'{expected_base}'."
            )
            raise AssertionError(errmsg)

        # --- Test 3: Relative path-based endpoint computation ---

        computed_rel_path = CustomPathBlueprint._compute_full_path(
            leaf=None, path=sub_path
        )

        expected_rel_path = f"{expected_base}/{sub_path}"

        if computed_rel_path != expected_rel_path:
            errmsg = (
                f"Iteration {iteration}: Relative path computation "
                f"failed. Expected '{expected_rel_path}', got "
                f"'{computed_rel_path}'."
            )
            raise AssertionError(errmsg)

        if not computed_rel_path.startswith(expected_base):
            errmsg = (
                f"Iteration {iteration}: Relative path "
                f"'{computed_rel_path}' does not start with base "
                f"'{expected_base}'."
            )
            raise AssertionError(errmsg)

        # --- Test 4: Absolute path-based endpoint computation ---

        abs_sub_path = f"/{sub_path}"
        computed_abs_path = CustomPathBlueprint._compute_full_path(
            leaf=None, path=abs_sub_path
        )

        expected_abs_path = f"{expected_base}{abs_sub_path}"

        if computed_abs_path != expected_abs_path:
            errmsg = (
                f"Iteration {iteration}: Absolute path computation "
                f"failed. Expected '{expected_abs_path}', got "
                f"'{computed_abs_path}'."
            )
            raise AssertionError(errmsg)

        if not computed_abs_path.startswith(expected_base):
            errmsg = (
                f"Iteration {iteration}: Absolute path "
                f"'{computed_abs_path}' does not start with base "
                f"'{expected_base}'."
            )
            raise AssertionError(errmsg)

        # --- Test 5: configure() changes base_path ---

        new_base_path = _random_base_path()

        # Ensure the new path is different from the original
        while new_base_path.rstrip("/") == base_path.rstrip("/"):
            new_base_path = _random_base_path()

        class ConfigurableBlueprint(SecurityBlueprint):
            pass

        ConfigurableBlueprint.base_path = base_path
        ConfigurableBlueprint.auth_system = None
        ConfigurableBlueprint.enabled_endpoints = None

        # Use configure to change the base_path
        from automojo.testbase.mocking import Mock
        mock_auth = Mock()
        mock_auth.configure(recursive=True)

        ConfigurableBlueprint.configure(
            auth_system=mock_auth,
            base_path=new_base_path,
        )

        new_resolved_base = ConfigurableBlueprint._get_base_path()
        expected_new_base = new_base_path.rstrip("/")

        if new_resolved_base != expected_new_base:
            errmsg = (
                f"Iteration {iteration}: After configure(), "
                f"_get_base_path returned '{new_resolved_base}', "
                f"expected '{expected_new_base}'."
            )
            raise AssertionError(errmsg)

        # Verify path computation uses the new base
        new_computed = ConfigurableBlueprint._compute_full_path(
            leaf=leaf_name, path=None
        )

        if not new_computed.startswith(expected_new_base):
            errmsg = (
                f"Iteration {iteration}: After configure(), computed "
                f"path '{new_computed}' does not start with new base "
                f"'{expected_new_base}'."
            )
            raise AssertionError(errmsg)

        # --- Test 6: Trailing slash handling ---

        trailing_base = base_path + "/"

        class TrailingSlashBlueprint(SecurityBlueprint):
            pass

        TrailingSlashBlueprint.base_path = trailing_base

        trailing_resolved = TrailingSlashBlueprint._get_base_path()

        if trailing_resolved.endswith("/"):
            errmsg = (
                f"Iteration {iteration}: _get_base_path did not strip "
                f"trailing slash. Got '{trailing_resolved}'."
            )
            raise AssertionError(errmsg)

        trailing_computed = TrailingSlashBlueprint._compute_full_path(
            leaf=leaf_name, path=None
        )

        if "//" in trailing_computed:
            errmsg = (
                f"Iteration {iteration}: Path contains double slash: "
                f"'{trailing_computed}'."
            )
            raise AssertionError(errmsg)

    return
