"""
    Unit tests for the OpenAPI specification caching module.

    This module tests the :class:`SpecificationCache` and
    :class:`CachedOpenAPIGenerator` classes.

    **Validates: Requirements 12.1, 12.2, 12.3, 12.4, 12.5, 12.6**
"""

import time

from typing import Any, Dict, List, Optional

from automojo.testbase.mocking import Mock

from automojo.webworks.openapi.cache import (
    CachedOpenAPIGenerator,
    SpecificationCache,
)
from automojo.webworks.openapi.configuration import OpenAPIInfo


# =============================================================================
# Helper Functions
# =============================================================================

class _HandlerStub:
    """
        A simple stub that provides a __name__ attribute for mock handlers.
    """

    def __init__(self, name):
        self.__name__ = name

    def __call__(self):
        pass


def _create_mock_constraints(access_policy=None):
    """
        Create a mock EndpointConstraints object.
    """
    mock_constraints = Mock()
    mock_constraints.configure(recursive=True)
    ctx = mock_constraints.mock_context()
    ctx.set_attribute("access_policy", access_policy)
    return mock_constraints


def _create_mock_descriptor(
    handler_name="test_handler",
    path="/test",
    methods=None,
    tags=None,
    doc=None,
    extras=None,
    constraints=None,
):
    """
        Create a mock EndpointDescriptor with the given attributes.
    """
    mock = Mock()
    mock.configure(recursive=True)
    ctx = mock.mock_context()

    handler = _HandlerStub(handler_name)

    ctx.set_attribute("handler", handler)
    ctx.set_attribute("module", "test_module")
    ctx.set_attribute("path", path)
    ctx.set_attribute("leaf", None)
    ctx.set_attribute("methods", methods or ["GET"])
    ctx.set_attribute("tags", tags or [])
    ctx.set_attribute("doc", doc)
    resolved_extras = extras or {}
    if "endpoint_type" not in resolved_extras:
        resolved_extras = dict(resolved_extras)
        resolved_extras["endpoint_type"] = "rest"
    ctx.set_attribute("extras", resolved_extras)
    ctx.set_attribute("constraints", constraints or _create_mock_constraints())
    ctx.set_attribute("version", None)

    return mock


def _create_mock_registry(descriptors):
    """
        Create a mock EndpointRegistry that returns the given descriptors.
    """
    mock_registry = Mock()
    mock_registry.configure(recursive=True)
    mock_registry.mock_context().mock_method("collect", return_value=descriptors)
    return mock_registry


def _create_default_info():
    """
        Create a default OpenAPIInfo for testing.
    """
    return OpenAPIInfo(title="Test API", version="1.0.0")


def _create_sample_spec():
    """
        Create a sample specification dictionary for cache testing.
    """
    spec = {
        "openapi": "3.0.3",
        "info": {"title": "Test API", "version": "1.0.0"},
        "paths": {},
    }
    return spec


# =============================================================================
# SpecificationCache Tests
# =============================================================================

def test_cache_get_returns_none_when_empty():
    """
        Verify that get() returns None when no specification has been cached.
    """
    cache = SpecificationCache()
    result = cache.get()

    if result is not None:
        errmsg = f"Expected None from empty cache, got {type(result)}"
        raise AssertionError(errmsg)

    return


def test_cache_set_and_get_returns_spec():
    """
        Verify that a cached specification can be retrieved.
    """
    cache = SpecificationCache()
    spec = _create_sample_spec()

    cache.set(spec)
    result = cache.get()

    if result is None:
        errmsg = "Expected cached spec, got None"
        raise AssertionError(errmsg)

    if result != spec:
        errmsg = f"Cached spec does not match original. Got: {result}"
        raise AssertionError(errmsg)

    return


def test_cache_invalidate_clears_cache():
    """
        Verify that invalidate() clears the cached specification.
    """
    cache = SpecificationCache()
    spec = _create_sample_spec()

    cache.set(spec)
    cache.invalidate()
    result = cache.get()

    if result is not None:
        errmsg = f"Expected None after invalidation, got {type(result)}"
        raise AssertionError(errmsg)

    return


def test_cache_ttl_returns_spec_before_expiry():
    """
        Verify that a cached spec is returned when TTL has not expired.
    """
    cache = SpecificationCache(ttl=10)
    spec = _create_sample_spec()

    cache.set(spec)
    result = cache.get()

    if result is None:
        errmsg = "Expected cached spec before TTL expiry, got None"
        raise AssertionError(errmsg)

    if result != spec:
        errmsg = "Cached spec does not match original before TTL expiry"
        raise AssertionError(errmsg)

    return


def test_cache_ttl_returns_none_after_expiry():
    """
        Verify that get() returns None after the TTL has expired.
    """
    cache = SpecificationCache(ttl=1)
    spec = _create_sample_spec()

    cache.set(spec)

    # Wait for the TTL to expire
    time.sleep(1.1)

    result = cache.get()

    if result is not None:
        errmsg = f"Expected None after TTL expiry, got spec"
        raise AssertionError(errmsg)

    return


def test_cache_production_mode_never_expires():
    """
        Verify that in production mode the cache never expires regardless
        of TTL.
    """
    cache = SpecificationCache(ttl=1, production_mode=True)
    spec = _create_sample_spec()

    cache.set(spec)

    # Wait longer than the TTL
    time.sleep(1.1)

    result = cache.get()

    if result is None:
        errmsg = "Expected cached spec in production mode, got None"
        raise AssertionError(errmsg)

    if result != spec:
        errmsg = "Cached spec does not match original in production mode"
        raise AssertionError(errmsg)

    return


def test_cache_no_ttl_does_not_expire():
    """
        Verify that when no TTL is set the cache does not expire on its own.
    """
    cache = SpecificationCache(ttl=None)
    spec = _create_sample_spec()

    cache.set(spec)
    result = cache.get()

    if result is None:
        errmsg = "Expected cached spec with no TTL, got None"
        raise AssertionError(errmsg)

    return


def test_cache_invalidate_resets_timestamp():
    """
        Verify that invalidate() clears both the cache and the timestamp.
    """
    cache = SpecificationCache(ttl=10)
    spec = _create_sample_spec()

    cache.set(spec)
    cache.invalidate()

    if cache._cache is not None:
        errmsg = "Expected _cache to be None after invalidation"
        raise AssertionError(errmsg)

    if cache._cache_time is not None:
        errmsg = "Expected _cache_time to be None after invalidation"
        raise AssertionError(errmsg)

    return


# =============================================================================
# CachedOpenAPIGenerator Tests
# =============================================================================

def test_cached_generator_returns_spec():
    """
        Verify that the cached generator produces a valid specification.
    """
    desc = _create_mock_descriptor(
        handler_name="get_items",
        path="/items",
        methods=["GET"],
        tags=["items"],
    )
    registry = _create_mock_registry([desc])
    info = _create_default_info()

    generator = CachedOpenAPIGenerator(
        registry=registry,
        info=info,
    )

    spec = generator.generate()

    if "openapi" not in spec:
        errmsg = "Generated spec missing 'openapi' key"
        raise AssertionError(errmsg)

    if spec["openapi"] != "3.0.3":
        errmsg = f"Expected openapi 3.0.3, got {spec['openapi']}"
        raise AssertionError(errmsg)

    return


def test_cached_generator_returns_cached_on_second_call():
    """
        Verify that the second call to generate() returns the cached spec
        without regenerating.
    """
    desc = _create_mock_descriptor(
        handler_name="get_items",
        path="/items",
        methods=["GET"],
        tags=["items"],
    )
    registry = _create_mock_registry([desc])
    info = _create_default_info()

    generator = CachedOpenAPIGenerator(
        registry=registry,
        info=info,
    )

    spec_1 = generator.generate()
    spec_2 = generator.generate()

    if spec_1 is not spec_2:
        errmsg = "Expected same object reference from cached generate()"
        raise AssertionError(errmsg)

    return


def test_cached_generator_refresh_invalidates_cache():
    """
        Verify that refresh() invalidates the cache so the next generate()
        rebuilds the specification.
    """
    desc = _create_mock_descriptor(
        handler_name="get_items",
        path="/items",
        methods=["GET"],
        tags=["items"],
    )
    registry = _create_mock_registry([desc])
    info = _create_default_info()

    generator = CachedOpenAPIGenerator(
        registry=registry,
        info=info,
    )

    spec_1 = generator.generate()
    generator.refresh()
    spec_2 = generator.generate()

    if spec_1 is spec_2:
        errmsg = "Expected different object after refresh(), got same reference"
        raise AssertionError(errmsg)

    if spec_1 != spec_2:
        errmsg = "Expected equivalent specs after refresh with same registry"
        raise AssertionError(errmsg)

    return


def test_cached_generator_production_mode():
    """
        Verify that production mode caching works through the generator.
    """
    desc = _create_mock_descriptor(
        handler_name="get_items",
        path="/items",
        methods=["GET"],
        tags=["items"],
    )
    registry = _create_mock_registry([desc])
    info = _create_default_info()

    generator = CachedOpenAPIGenerator(
        registry=registry,
        info=info,
        cache_ttl=1,
        production_mode=True,
    )

    spec_1 = generator.generate()

    # Wait longer than TTL
    time.sleep(1.1)

    spec_2 = generator.generate()

    if spec_1 is not spec_2:
        errmsg = "Expected same cached object in production mode after TTL"
        raise AssertionError(errmsg)

    return


def test_cached_generator_auto_invalidates_on_registry_change():
    """
        Verify that in development mode the cache is automatically
        invalidated when the endpoint registry changes.
    """
    desc_1 = _create_mock_descriptor(
        handler_name="get_items",
        path="/items",
        methods=["GET"],
        tags=["items"],
    )

    # Start with one descriptor
    descriptors = [desc_1]
    registry = Mock()
    registry.configure(recursive=True)

    call_count = [0]

    def collect_side_effect():
        return list(descriptors)

    registry.mock_context().mock_method("collect", side_effect=collect_side_effect)

    info = _create_default_info()

    generator = CachedOpenAPIGenerator(
        registry=registry,
        info=info,
        production_mode=False,
    )

    spec_1 = generator.generate()

    # Add a second descriptor to simulate a registry change
    desc_2 = _create_mock_descriptor(
        handler_name="get_users",
        path="/users",
        methods=["GET"],
        tags=["users"],
    )
    descriptors.append(desc_2)

    spec_2 = generator.generate()

    # The cache should have been invalidated due to endpoint count change
    if spec_1 is spec_2:
        errmsg = (
            "Expected different spec object after registry change, "
            "got same reference"
        )
        raise AssertionError(errmsg)

    return


def test_cached_generator_no_invalidation_in_production_mode():
    """
        Verify that in production mode the cache is NOT invalidated when
        the endpoint registry changes.
    """
    desc_1 = _create_mock_descriptor(
        handler_name="get_items",
        path="/items",
        methods=["GET"],
        tags=["items"],
    )

    descriptors = [desc_1]
    registry = Mock()
    registry.configure(recursive=True)

    def collect_side_effect():
        return list(descriptors)

    registry.mock_context().mock_method("collect", side_effect=collect_side_effect)

    info = _create_default_info()

    generator = CachedOpenAPIGenerator(
        registry=registry,
        info=info,
        production_mode=True,
    )

    spec_1 = generator.generate()

    # Add a second descriptor
    desc_2 = _create_mock_descriptor(
        handler_name="get_users",
        path="/users",
        methods=["GET"],
        tags=["users"],
    )
    descriptors.append(desc_2)

    spec_2 = generator.generate()

    # In production mode the cache should NOT be invalidated
    if spec_1 is not spec_2:
        errmsg = (
            "Expected same cached object in production mode despite "
            "registry change"
        )
        raise AssertionError(errmsg)

    return


def test_cached_generator_with_ttl():
    """
        Verify that the cached generator respects TTL in development mode.
    """
    desc = _create_mock_descriptor(
        handler_name="get_items",
        path="/items",
        methods=["GET"],
        tags=["items"],
    )
    registry = _create_mock_registry([desc])
    info = _create_default_info()

    generator = CachedOpenAPIGenerator(
        registry=registry,
        info=info,
        cache_ttl=1,
        production_mode=False,
    )

    spec_1 = generator.generate()

    # Wait for TTL to expire
    time.sleep(1.1)

    spec_2 = generator.generate()

    if spec_1 is spec_2:
        errmsg = "Expected different object after TTL expiry"
        raise AssertionError(errmsg)

    return
