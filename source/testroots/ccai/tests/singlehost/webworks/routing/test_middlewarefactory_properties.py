"""
.. module:: test_middlewarefactory_properties
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: Property-based tests for middleware factory helpers.

.. moduleauthor:: Code Craft AI LLC

This module contains property-based tests for the ``create_middleware``
factory helper, validating Property 22: create_middleware returns
protocol-conforming instances.
"""

__author__ = "Code Craft AI LLC"
__copyright__ = "Copyright 2025, Code Craft AI LLC"
__credits__ = []

from typing import Callable, Dict

import ccai.testbase as testbase

from ccai.testbase.properties import given
from ccai.testbase.properties import strategies as st

from ccai.webworks.routing.middleware import AsyncMiddleware, Middleware
from ccai.webworks.routing.middlewarefactory import create_middleware
from ccai.webworks.routing.middlewareregistry import MiddlewareRegistry
from ccai.webworks.routing.request import Request


# =============================================================================
# Test Helpers
# =============================================================================

class MockResponse:
    """
        Minimal Response implementation for property tests.
    """

    def __init__(self, status_code: int = 200, body: bytes = b"", headers: Dict[str, str] = None):
        self._status_code = status_code
        self._body = body
        self._headers = headers or {}
        return

    @property
    def status_code(self) -> int:
        return self._status_code

    @property
    def body(self) -> bytes:
        return self._body

    @property
    def headers(self) -> Dict[str, str]:
        return self._headers


class SyncMiddlewareFromFactory:
    """
        A sync middleware class produced by a factory.
    """

    def __init__(self, mw_name: str, tag: str = "default"):
        self.name = mw_name
        self.tag = tag
        return

    def __call__(self, request: Request, call_next: Callable) -> MockResponse:
        return call_next(request)


class AsyncMiddlewareFromFactory:
    """
        An async middleware class produced by a factory.
    """

    def __init__(self, mw_name: str, tag: str = "default"):
        self.name = mw_name
        self.tag = tag
        return

    async def __call__(self, request, call_next):
        return await call_next(request)


def sync_factory(mw_name: str = "sync_mw", tag: str = "default"):
    """
        Factory that produces a sync middleware instance.
    """
    return SyncMiddlewareFromFactory(mw_name=mw_name, tag=tag)


def async_factory(mw_name: str = "async_mw", tag: str = "default"):
    """
        Factory that produces an async middleware instance.
    """
    return AsyncMiddlewareFromFactory(mw_name=mw_name, tag=tag)


def bad_factory(mw_name: str = "bad"):
    """
        Factory that returns a non-conforming object (an integer).
    """
    return 42


def callable_factory(mw_name: str = "callable_mw"):
    """
        Factory that returns a plain callable with (request, call_next) signature.
    """
    def middleware(request, call_next):
        return call_next(request)
    middleware.name = mw_name
    return middleware


# =============================================================================
# Property 22: create_middleware returns protocol-conforming instance
# =============================================================================

@given(
    name=st.text(min_size=1, max_size=20, alphabet="abcdefghijklmnopqrstuvwxyz"),
    tag=st.text(min_size=1, max_size=10, alphabet="abcdefghijklmnopqrstuvwxyz0123456789"),
    constraints={"max_examples": 50}
)
def test_property_create_middleware_sync_factory_returns_conforming_instance(name, tag):
    """
        Property 22: create_middleware with a sync factory returns an instance
        that conforms to the Middleware protocol.
    """
    instance = create_middleware(sync_factory, mw_name=name, tag=tag)

    is_conforming = isinstance(instance, Middleware) or callable(instance)
    testbase.assert_true(
        is_conforming,
        f"create_middleware should return a protocol-conforming instance, "
        f"got {type(instance).__name__} for name={name!r}, tag={tag!r}."
    )

    testbase.assert_equal(
        instance.name, name,
        f"Middleware name should be {name!r}, got {instance.name!r}."
    )

    testbase.assert_equal(
        instance.tag, tag,
        f"Middleware tag should be {tag!r}, got {instance.tag!r}."
    )
    return


@given(
    name=st.text(min_size=1, max_size=20, alphabet="abcdefghijklmnopqrstuvwxyz"),
    tag=st.text(min_size=1, max_size=10, alphabet="abcdefghijklmnopqrstuvwxyz0123456789"),
    constraints={"max_examples": 50}
)
def test_property_create_middleware_async_factory_returns_conforming_instance(name, tag):
    """
        Property 22: create_middleware with an async factory returns an instance
        that conforms to the AsyncMiddleware protocol.
    """
    instance = create_middleware(async_factory, mw_name=name, tag=tag)

    is_conforming = isinstance(instance, AsyncMiddleware) or callable(instance)
    testbase.assert_true(
        is_conforming,
        f"create_middleware should return a protocol-conforming instance, "
        f"got {type(instance).__name__} for name={name!r}, tag={tag!r}."
    )

    testbase.assert_equal(
        instance.name, name,
        f"Middleware name should be {name!r}, got {instance.name!r}."
    )
    return


@given(
    name=st.text(min_size=1, max_size=20, alphabet="abcdefghijklmnopqrstuvwxyz"),
    constraints={"max_examples": 50}
)
def test_property_create_middleware_callable_factory_returns_conforming_instance(name):
    """
        Property 22: create_middleware with a factory returning a plain callable
        produces a valid middleware.
    """
    instance = create_middleware(callable_factory, mw_name=name)

    testbase.assert_true(
        callable(instance),
        f"create_middleware should return a callable instance, "
        f"got {type(instance).__name__} for name={name!r}."
    )
    return


@given(
    name=st.text(min_size=1, max_size=20, alphabet="abcdefghijklmnopqrstuvwxyz"),
    constraints={"max_examples": 30}
)
def test_property_create_middleware_rejects_non_conforming_factory_output(name):
    """
        Property 22: create_middleware raises TypeError when the factory
        returns a non-conforming object.
    """
    raised = False
    try:
        create_middleware(bad_factory, mw_name=name)
    except TypeError:
        raised = True

    testbase.assert_true(
        raised,
        f"create_middleware should raise TypeError for non-conforming factory "
        f"output, but did not for name={name!r}."
    )
    return


# =============================================================================
# Factory integration with MiddlewareRegistry
# =============================================================================

@given(
    name=st.text(min_size=1, max_size=20, alphabet="abcdefghijklmnopqrstuvwxyz"),
    tag=st.text(min_size=1, max_size=10, alphabet="abcdefghijklmnopqrstuvwxyz0123456789"),
    constraints={"max_examples": 50}
)
def test_property_registry_factory_registration_produces_middleware_in_pipeline(name, tag):
    """
        When a factory is registered with the MiddlewareRegistry, the
        registry invokes the factory and adds the resulting middleware
        to the pipeline.
    """
    registry = MiddlewareRegistry()
    registry.register(
        middleware=None,
        name=name,
        factory=sync_factory,
        factory_config={"mw_name": name, "tag": tag},
    )

    entries = registry.get_middleware_by_scope("global")
    testbase.assert_equal(
        len(entries), 1,
        f"Registry should contain 1 entry after factory registration, "
        f"got {len(entries)}."
    )

    entry = entries[0]
    testbase.assert_equal(
        entry.name, name,
        f"Registered middleware name should be {name!r}, got {entry.name!r}."
    )

    testbase.assert_true(
        isinstance(entry.middleware, SyncMiddlewareFromFactory),
        f"Registered middleware should be a SyncMiddlewareFromFactory instance, "
        f"got {type(entry.middleware).__name__}."
    )

    testbase.assert_equal(
        entry.middleware.tag, tag,
        f"Registered middleware tag should be {tag!r}, got {entry.middleware.tag!r}."
    )
    return


@given(
    name=st.text(min_size=1, max_size=20, alphabet="abcdefghijklmnopqrstuvwxyz"),
    constraints={"max_examples": 30}
)
def test_property_registry_factory_registration_rejects_bad_factory(name):
    """
        When a factory registered with the MiddlewareRegistry returns a
        non-conforming object, registration raises TypeError.
    """
    registry = MiddlewareRegistry()
    raised = False
    try:
        registry.register(
            middleware=None,
            name=name,
            factory=bad_factory,
            factory_config={"mw_name": name},
        )
    except TypeError:
        raised = True

    testbase.assert_true(
        raised,
        f"Registry should raise TypeError for non-conforming factory output, "
        f"but did not for name={name!r}."
    )
    return


if __name__ == "__main__":
    from ccai.testbase.entrypoints import generic_test_entrypoint
    generic_test_entrypoint()
