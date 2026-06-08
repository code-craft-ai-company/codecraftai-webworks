"""
    .. module:: cache
        :platform: Darwin, Linux, Unix, Windows
        :synopsis: Specification caching for OpenAPI generation.

    .. moduleauthor:: Code Craft AI LLC

This module provides caching support for OpenAPI specification generation.
The :class:`SpecificationCache` handles time-based and production-mode caching,
while :class:`CachedOpenAPIGenerator` extends the base generator with transparent
cache integration and automatic invalidation on endpoint changes.
"""

__author__ = "Code Craft AI LLC"
__copyright__ = "Copyright 2025, Code Craft AI LLC"
__credits__ = []

import time

from typing import Any, Dict, Optional

from ccai.webworks.openapi.generator import OpenAPIGenerator


class SpecificationCache:
    """
        Caches generated OpenAPI specifications with support for TTL-based
        expiration and production mode (indefinite caching).

        In production mode the cache never expires, regardless of the TTL
        setting.  In development mode the cache respects the configured TTL
        and returns ``None`` once the entry has expired.

        :param ttl: Time-to-live in seconds.  When ``None`` the cache does
            not expire based on time (but can still be invalidated manually).
        :param production_mode: When ``True`` the cache never expires.
    """

    def __init__(self, ttl: Optional[int] = None, production_mode: bool = False):
        self.ttl = ttl
        self.production_mode = production_mode
        self._cache: Optional[Dict[str, Any]] = None
        self._cache_time: Optional[float] = None
        return

    def get(self) -> Optional[Dict[str, Any]]:
        """
            Return the cached specification if it is still valid.

            In production mode the cached value is always returned (it never
            expires).  In development mode the TTL is checked and the cache
            is invalidated when the entry has exceeded its time-to-live.

            :returns: The cached specification dictionary, or ``None`` when
                the cache is empty or has expired.
        """
        if self._cache is None:
            return None

        if self.production_mode:
            return self._cache

        if self.ttl is not None and self._cache_time is not None:
            elapsed = time.time() - self._cache_time
            if elapsed > self.ttl:
                self.invalidate()
                return None

        return self._cache

    def set(self, spec: Dict[str, Any]) -> None:
        """
            Store a specification in the cache with the current timestamp.

            :param spec: The OpenAPI specification dictionary to cache.
        """
        self._cache = spec
        self._cache_time = time.time()
        return

    def invalidate(self) -> None:
        """
            Clear the cached specification and its timestamp.
        """
        self._cache = None
        self._cache_time = None
        return


class CachedOpenAPIGenerator(OpenAPIGenerator):
    """
        An OpenAPI generator that transparently caches the generated
        specification.

        On the first call to :meth:`generate` the specification is built
        by the parent class and stored in a :class:`SpecificationCache`.
        Subsequent calls return the cached copy until the cache is
        invalidated.

        In development mode the generator automatically detects when the
        endpoint registry has changed (by tracking the number of registered
        endpoints) and invalidates the cache so the next call to
        :meth:`generate` produces an up-to-date specification.

        :param registry: The endpoint registry to generate from.
        :param info: The OpenAPI info configuration.
        :param cache_ttl: Optional time-to-live in seconds for the cache.
        :param production_mode: When ``True`` the cache never expires.
        :param kwargs: Additional keyword arguments forwarded to
            :class:`OpenAPI_Generator`.
    """

    def __init__(
        self,
        registry,
        info,
        cache_ttl: Optional[int] = None,
        production_mode: bool = False,
        **kwargs,
    ):
        super().__init__(registry, info, **kwargs)
        self._spec_cache = SpecificationCache(
            ttl=cache_ttl,
            production_mode=production_mode,
        )
        self._last_endpoint_count: Optional[int] = None
        return

    def generate(self) -> Dict[str, Any]:
        """
            Generate the OpenAPI specification with caching support.

            When the cache contains a valid entry it is returned directly.
            Otherwise the specification is generated via the parent class,
            stored in the cache, and then returned.

            In development mode (``production_mode=False``) the endpoint
            registry is checked for changes before returning a cached value.
            If the number of registered endpoints has changed the cache is
            automatically invalidated.

            :returns: The OpenAPI specification dictionary.
        """
        # In development mode, detect registry changes and auto-invalidate
        if not self._spec_cache.production_mode:
            self._check_registry_changes()

        cached = self._spec_cache.get()
        if cached is not None:
            return cached

        spec = super().generate()
        self._spec_cache.set(spec)
        self._last_endpoint_count = self._get_endpoint_count()
        return spec

    def refresh(self) -> None:
        """
            Invalidate the cached specification.

            The next call to :meth:`generate` will rebuild the specification
            from the current registry state.
        """
        self._spec_cache.invalidate()
        self._last_endpoint_count = None
        return

    # -----------------------------------------------------------------
    # Private helpers
    # -----------------------------------------------------------------

    def _check_registry_changes(self) -> None:
        """
            Compare the current endpoint count against the last known count
            and invalidate the cache when they differ.
        """
        if self._last_endpoint_count is None:
            return

        current_count = self._get_endpoint_count()
        if current_count != self._last_endpoint_count:
            self._spec_cache.invalidate()
        return

    def _get_endpoint_count(self) -> int:
        """
            Return the number of endpoints currently in the registry.

            :returns: The endpoint count.
        """
        descriptors = self.registry.collect()
        count = len(descriptors)
        return count
