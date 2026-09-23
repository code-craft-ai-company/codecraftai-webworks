"""
    Tests for extension points functionality.

    This module contains unit tests and property-based tests for the
    extension_point decorator, contribute_to() method, and
    get_contributions() method in the ExtensionRegistry.
"""

import logging
import random
import string

from typing import Any, Dict, List, Optional

from ccai.webworks.extensibility.datastructures import ExtensionPointDefinition
from ccai.webworks.extensibility.decorators import clear_registered_extension_points
from ccai.webworks.extensibility.decorators import extension_point
from ccai.webworks.extensibility.decorators import get_registered_extension_points
from ccai.webworks.extensibility.exceptions import ExtensionPointError
from ccai.webworks.extensibility.registry import ExtensionRegistry


# =============================================================================
# Test Helpers
# =============================================================================

class _FakeAppContext:
    """
        A fake application context for testing purposes.

        Provides the duck-typed interface that ExtensionRegistry
        and ExtensionContext expect from the application context.
    """

    def __init__(
        self,
        config: Optional[Any] = None,
        endpoint_registry: Optional[Any] = None,
        url_node_map: Optional[Any] = None,
        middleware: Optional[List[Any]] = None,
        extension_registry: Optional[Any] = None
    ):
        self.config = config if config is not None else {}
        self.endpoint_registry = endpoint_registry
        self.url_node_map = url_node_map
        self.middleware = middleware if middleware is not None else []
        self.extension_registry = extension_registry
        self._loggers: Dict[str, logging.Logger] = {}
        return

    def get_logger(self, name: str) -> logging.Logger:
        """
            Get a logger by name.

            :param name: The logger name.

            :returns: A Logger instance.
        """
        if name not in self._loggers:
            self._loggers[name] = logging.getLogger(name)

        rtnval = self._loggers[name]
        return rtnval


class _SampleInterface:
    """
        A sample interface class for extension point testing.

        Contributions to extension points using this interface must
        be instances of this class or its subclasses.
    """

    def process(self, data: Any) -> Any:
        """
            Process the given data.

            :param data: The data to process.

            :returns: The processed data.
        """
        return data


class _ValidContribution(_SampleInterface):
    """
        A valid contribution that implements _SampleInterface.
    """

    def __init__(self, name: str = "default"):
        self._name = name
        return

    def process(self, data: Any) -> Any:
        """
            Process the given data by prefixing with the contribution name.

            :param data: The data to process.

            :returns: The processed data.
        """
        rtnval = "{}: {}".format(self._name, data)
        return rtnval


class _InvalidContribution:
    """
        An invalid contribution that does NOT implement _SampleInterface.
    """

    def __init__(self, value: str = "invalid"):
        self._value = value
        return


def _generate_random_string(min_length: int = 1, max_length: int = 20) -> str:
    """
        Generate a random string of alphanumeric characters.

        :param min_length: Minimum length of the generated string.
        :param max_length: Maximum length of the generated string.

        :returns: A random alphanumeric string.
    """
    length = random.randint(min_length, max_length)
    result = "".join(random.choices(string.ascii_lowercase + string.digits, k=length))
    return result


# =============================================================================
# Unit Tests for extension_point decorator
# =============================================================================

def test_extension_point_decorator_registers_definition():
    """
        Verify that the @extension_point decorator registers an
        ExtensionPointDefinition in the module-level registry.
    """
    clear_registered_extension_points()

    @extension_point(name="test-point", interface=_SampleInterface, description="A test point")
    class MyExtensionProvider:
        pass

    definitions = get_registered_extension_points()

    if "test-point" not in definitions:
        raise AssertionError("Expected 'test-point' in registered extension points")

    defn = definitions["test-point"]

    if defn.name != "test-point":
        raise AssertionError("Expected definition name 'test-point', got '{}'".format(defn.name))

    if defn.interface is not _SampleInterface:
        raise AssertionError("Expected interface to be _SampleInterface")

    if defn.description != "A test point":
        raise AssertionError("Expected description 'A test point', got '{}'".format(defn.description))

    clear_registered_extension_points()
    return


def test_extension_point_decorator_returns_target_unchanged():
    """
        Verify that the @extension_point decorator returns the
        decorated class unchanged.
    """
    clear_registered_extension_points()

    class OriginalClass:
        pass

    decorated = extension_point(
        name="unchanged-point",
        interface=_SampleInterface
    )(OriginalClass)

    if decorated is not OriginalClass:
        raise AssertionError("Expected decorator to return the original class unchanged")

    clear_registered_extension_points()
    return


# =============================================================================
# Unit Tests for contribute_to()
# =============================================================================

def test_contribute_to_adds_contribution():
    """
        Verify that contribute_to() adds a contribution to the
        extension point's contribution list.
    """
    app_ctx = _FakeAppContext()
    registry = ExtensionRegistry(app_context=app_ctx)

    definition = ExtensionPointDefinition(
        name="test-point",
        interface=_SampleInterface,
        description="A test point"
    )
    registry.register_extension_point(definition)

    contribution = _ValidContribution(name="contrib-1")
    registry.contribute_to("test-point", contribution)

    contributions = registry.get_contributions("test-point")

    if len(contributions) != 1:
        raise AssertionError("Expected 1 contribution, got {}".format(len(contributions)))

    if contributions[0] is not contribution:
        raise AssertionError("Expected the same contribution instance")

    return


def test_contribute_to_raises_for_unknown_point():
    """
        Verify that contribute_to() raises ExtensionPointError
        when the extension point is not registered.
    """
    app_ctx = _FakeAppContext()
    registry = ExtensionRegistry(app_context=app_ctx)

    contribution = _ValidContribution()

    raised = False
    try:
        registry.contribute_to("nonexistent-point", contribution)
    except ExtensionPointError:
        raised = True

    if raised is not True:
        raise AssertionError("Expected ExtensionPointError for unknown extension point")

    return


def test_contribute_to_raises_for_invalid_interface():
    """
        Verify that contribute_to() raises ExtensionPointError
        when the contribution does not implement the required interface.
    """
    app_ctx = _FakeAppContext()
    registry = ExtensionRegistry(app_context=app_ctx)

    definition = ExtensionPointDefinition(
        name="typed-point",
        interface=_SampleInterface,
        description="A typed point"
    )
    registry.register_extension_point(definition)

    invalid = _InvalidContribution()

    raised = False
    try:
        registry.contribute_to("typed-point", invalid)
    except ExtensionPointError:
        raised = True

    if raised is not True:
        raise AssertionError("Expected ExtensionPointError for invalid interface")

    return


def test_contribute_to_allows_valid_interface():
    """
        Verify that contribute_to() accepts a contribution that
        implements the required interface.
    """
    app_ctx = _FakeAppContext()
    registry = ExtensionRegistry(app_context=app_ctx)

    definition = ExtensionPointDefinition(
        name="typed-point",
        interface=_SampleInterface,
        description="A typed point"
    )
    registry.register_extension_point(definition)

    valid = _ValidContribution(name="valid-contrib")
    registry.contribute_to("typed-point", valid)

    contributions = registry.get_contributions("typed-point")

    if len(contributions) != 1:
        raise AssertionError("Expected 1 contribution, got {}".format(len(contributions)))

    return


# =============================================================================
# Unit Tests for get_contributions()
# =============================================================================

def test_get_contributions_returns_empty_for_no_contributions():
    """
        Verify that get_contributions() returns an empty list when
        no contributions have been made to the extension point.
    """
    app_ctx = _FakeAppContext()
    registry = ExtensionRegistry(app_context=app_ctx)

    definition = ExtensionPointDefinition(
        name="empty-point",
        interface=_SampleInterface,
        description="An empty point"
    )
    registry.register_extension_point(definition)

    contributions = registry.get_contributions("empty-point")

    if len(contributions) != 0:
        raise AssertionError("Expected 0 contributions, got {}".format(len(contributions)))

    return


def test_get_contributions_returns_empty_for_unknown_point():
    """
        Verify that get_contributions() returns an empty list when
        the extension point is not registered.
    """
    app_ctx = _FakeAppContext()
    registry = ExtensionRegistry(app_context=app_ctx)

    contributions = registry.get_contributions("unknown-point")

    if len(contributions) != 0:
        raise AssertionError("Expected 0 contributions for unknown point, got {}".format(len(contributions)))

    return


def test_get_contributions_returns_multiple():
    """
        Verify that get_contributions() returns all contributions
        made to an extension point.
    """
    app_ctx = _FakeAppContext()
    registry = ExtensionRegistry(app_context=app_ctx)

    definition = ExtensionPointDefinition(
        name="multi-point",
        interface=_SampleInterface,
        description="A multi-contribution point"
    )
    registry.register_extension_point(definition)

    contrib_a = _ValidContribution(name="a")
    contrib_b = _ValidContribution(name="b")
    contrib_c = _ValidContribution(name="c")

    registry.contribute_to("multi-point", contrib_a)
    registry.contribute_to("multi-point", contrib_b)
    registry.contribute_to("multi-point", contrib_c)

    contributions = registry.get_contributions("multi-point")

    if len(contributions) != 3:
        raise AssertionError("Expected 3 contributions, got {}".format(len(contributions)))

    if contributions[0] is not contrib_a:
        raise AssertionError("Expected first contribution to be contrib_a")

    if contributions[1] is not contrib_b:
        raise AssertionError("Expected second contribution to be contrib_b")

    if contributions[2] is not contrib_c:
        raise AssertionError("Expected third contribution to be contrib_c")

    return


# =============================================================================
# Property Tests
# =============================================================================

def test_property_30_extension_point_contribution():
    """
        Property 30: Extension Point Contribution

        For any extension point declared with @extension_point,
        contributions made via contribute_to() SHALL be retrievable
        via get_contributions().

        **Validates: Requirements 13.1, 13.3, 13.4**
    """
    for iteration in range(100):
        clear_registered_extension_points()

        app_ctx = _FakeAppContext()
        registry = ExtensionRegistry(app_context=app_ctx)

        # Generate a random extension point name
        point_name = "point-" + _generate_random_string(3, 15)

        # Use the decorator to declare the extension point
        @extension_point(name=point_name, interface=_SampleInterface)
        class _DynamicProvider:
            pass

        # Verify the decorator registered the definition
        definitions = get_registered_extension_points()
        if point_name not in definitions:
            errmsg = "Iteration {}: Extension point '{}' not found in decorator registry".format(
                iteration, point_name
            )
            raise AssertionError(errmsg)

        # Register the extension point in the registry
        defn = definitions[point_name]
        registry.register_extension_point(defn)

        # Generate a random number of contributions
        contrib_count = random.randint(1, 8)
        expected_contributions = []

        for contrib_idx in range(contrib_count):
            contrib_name = "contrib-{}-{}".format(iteration, contrib_idx)
            contrib = _ValidContribution(name=contrib_name)
            registry.contribute_to(point_name, contrib)
            expected_contributions.append(contrib)

        # Retrieve contributions
        retrieved = registry.get_contributions(point_name)

        # Verify count matches
        if len(retrieved) != contrib_count:
            errmsg = "Iteration {}: Expected {} contributions, got {}".format(
                iteration, contrib_count, len(retrieved)
            )
            raise AssertionError(errmsg)

        # Verify each contribution is the same instance in order
        for idx in range(contrib_count):
            if retrieved[idx] is not expected_contributions[idx]:
                errmsg = (
                    "Iteration {}: Contribution at index {} is not the "
                    "expected instance".format(iteration, idx)
                )
                raise AssertionError(errmsg)

    clear_registered_extension_points()
    return


def test_property_31_extension_point_interface_validation():
    """
        Property 31: Extension Point Interface Validation

        For any contribution to an extension point, the framework
        SHALL validate that it implements the required interface and
        raise ExtensionPointError if it does not.

        **Validates: Requirements 13.5, 13.6**
    """
    for iteration in range(100):
        app_ctx = _FakeAppContext()
        registry = ExtensionRegistry(app_context=app_ctx)

        # Generate a random extension point name
        point_name = "typed-point-" + _generate_random_string(3, 15)

        definition = ExtensionPointDefinition(
            name=point_name,
            interface=_SampleInterface,
            description="Typed point for iteration {}".format(iteration)
        )
        registry.register_extension_point(definition)

        # Valid contribution should succeed
        valid = _ValidContribution(name="valid-{}".format(iteration))
        raised_on_valid = False
        try:
            registry.contribute_to(point_name, valid)
        except ExtensionPointError:
            raised_on_valid = True

        if raised_on_valid is True:
            errmsg = (
                "Iteration {}: ExtensionPointError raised for valid "
                "contribution to '{}'".format(iteration, point_name)
            )
            raise AssertionError(errmsg)

        # Invalid contribution should raise ExtensionPointError
        invalid = _InvalidContribution(value="invalid-{}".format(iteration))
        raised_on_invalid = False
        try:
            registry.contribute_to(point_name, invalid)
        except ExtensionPointError:
            raised_on_invalid = True

        if raised_on_invalid is not True:
            errmsg = (
                "Iteration {}: Expected ExtensionPointError for invalid "
                "contribution to '{}'".format(iteration, point_name)
            )
            raise AssertionError(errmsg)

        # Verify only the valid contribution was stored
        contributions = registry.get_contributions(point_name)
        if len(contributions) != 1:
            errmsg = (
                "Iteration {}: Expected 1 contribution after valid + invalid, "
                "got {}".format(iteration, len(contributions))
            )
            raise AssertionError(errmsg)

        if contributions[0] is not valid:
            errmsg = "Iteration {}: Stored contribution is not the valid instance".format(iteration)
            raise AssertionError(errmsg)

    return
