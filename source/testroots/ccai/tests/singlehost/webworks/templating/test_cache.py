"""
    Tests for the TemplateCache class.
    
    This module tests the TemplateCache including:
    - Basic get/set operations
    - Cache size limits and LRU eviction
    - Auto-reload mode with staleness detection
    - Clear and remove operations
    - Edge cases and boundary conditions
"""

import time

from ccai.webworks.templating.cache import CacheEntry, TemplateCache


# =============================================================================
# CacheEntry Tests
# =============================================================================

def test_cache_entry_stores_template():
    """
        Test that CacheEntry stores the template object.
    """
    template = {"compiled": True}
    entry = CacheEntry(template=template)
    
    if entry.template != template:
        raise AssertionError(f"Expected {template}, got {entry.template}")
    
    return


def test_cache_entry_stores_mtime():
    """
        Test that CacheEntry stores the modification time.
    """
    template = {"compiled": True}
    mtime = 1234567890.0
    entry = CacheEntry(template=template, mtime=mtime)
    
    if entry.mtime != mtime:
        raise AssertionError(f"Expected {mtime}, got {entry.mtime}")
    
    return


def test_cache_entry_mtime_defaults_to_none():
    """
        Test that CacheEntry mtime defaults to None.
    """
    template = {"compiled": True}
    entry = CacheEntry(template=template)
    
    if entry.mtime is not None:
        raise AssertionError(f"Expected None, got {entry.mtime}")
    
    return


# =============================================================================
# __init__() Method Tests
# =============================================================================

def test_init_with_default_values():
    """
        Test that __init__() uses default values.
    """
    cache = TemplateCache()
    
    if cache.max_size != 400:
        raise AssertionError(f"Expected max_size 400, got {cache.max_size}")
    
    if cache.auto_reload is not False:
        raise AssertionError(f"Expected auto_reload False, got {cache.auto_reload}")
    
    if cache.size != 0:
        raise AssertionError(f"Expected size 0, got {cache.size}")
    
    return


def test_init_with_custom_max_size():
    """
        Test that __init__() accepts custom max_size.
    """
    cache = TemplateCache(max_size=100)
    
    if cache.max_size != 100:
        raise AssertionError(f"Expected max_size 100, got {cache.max_size}")
    
    return


def test_init_with_auto_reload_enabled():
    """
        Test that __init__() accepts auto_reload=True.
    """
    cache = TemplateCache(auto_reload=True)
    
    if cache.auto_reload is not True:
        raise AssertionError(f"Expected auto_reload True, got {cache.auto_reload}")
    
    return


def test_init_with_zero_max_size():
    """
        Test that __init__() accepts max_size=0.
    """
    cache = TemplateCache(max_size=0)
    
    if cache.max_size != 0:
        raise AssertionError(f"Expected max_size 0, got {cache.max_size}")
    
    return


# =============================================================================
# set() Method Tests
# =============================================================================

def test_set_stores_template():
    """
        Test that set() stores a template in the cache.
    """
    cache = TemplateCache()
    template = {"compiled": True}
    
    cache.set("index.html", template)
    
    if cache.size != 1:
        raise AssertionError(f"Expected size 1, got {cache.size}")
    
    return


def test_set_stores_template_with_mtime():
    """
        Test that set() stores a template with modification time.
    """
    cache = TemplateCache()
    template = {"compiled": True}
    mtime = 1234567890.0
    
    cache.set("index.html", template, mtime=mtime)
    
    if cache.size != 1:
        raise AssertionError(f"Expected size 1, got {cache.size}")
    
    return


def test_set_overwrites_existing_entry():
    """
        Test that set() overwrites an existing cache entry.
    """
    cache = TemplateCache()
    template1 = {"version": 1}
    template2 = {"version": 2}
    
    cache.set("index.html", template1)
    cache.set("index.html", template2)
    
    if cache.size != 1:
        raise AssertionError(f"Expected size 1, got {cache.size}")
    
    result = cache.get("index.html")
    if result != template2:
        raise AssertionError(f"Expected {template2}, got {result}")
    
    return


def test_set_multiple_templates():
    """
        Test that set() can store multiple templates.
    """
    cache = TemplateCache()
    
    cache.set("index.html", {"name": "index"})
    cache.set("about.html", {"name": "about"})
    cache.set("contact.html", {"name": "contact"})
    
    if cache.size != 3:
        raise AssertionError(f"Expected size 3, got {cache.size}")
    
    return


def test_set_evicts_lru_when_at_capacity():
    """
        Test that set() evicts least recently used when at capacity.
    """
    cache = TemplateCache(max_size=2)
    
    cache.set("first.html", {"name": "first"})
    cache.set("second.html", {"name": "second"})
    cache.set("third.html", {"name": "third"})
    
    if cache.size != 2:
        raise AssertionError(f"Expected size 2, got {cache.size}")
    
    # First should be evicted
    result = cache.get("first.html")
    if result is not None:
        raise AssertionError("first.html should have been evicted")
    
    # Second and third should still be present
    if cache.get("second.html") is None:
        raise AssertionError("second.html should be in cache")
    
    if cache.get("third.html") is None:
        raise AssertionError("third.html should be in cache")
    
    return


def test_set_with_zero_max_size_does_not_store():
    """
        Test that set() does not store when max_size is 0.
    """
    cache = TemplateCache(max_size=0)
    
    cache.set("index.html", {"compiled": True})
    
    if cache.size != 0:
        raise AssertionError(f"Expected size 0, got {cache.size}")
    
    return


# =============================================================================
# get() Method Tests
# =============================================================================

def test_get_returns_cached_template():
    """
        Test that get() returns a cached template.
    """
    cache = TemplateCache()
    template = {"compiled": True}
    
    cache.set("index.html", template)
    result = cache.get("index.html")
    
    if result != template:
        raise AssertionError(f"Expected {template}, got {result}")
    
    return


def test_get_returns_none_for_missing_key():
    """
        Test that get() returns None for missing key.
    """
    cache = TemplateCache()
    
    result = cache.get("missing.html")
    
    if result is not None:
        raise AssertionError(f"Expected None, got {result}")
    
    return


def test_get_updates_lru_order():
    """
        Test that get() updates LRU order.
    """
    cache = TemplateCache(max_size=2)
    
    cache.set("first.html", {"name": "first"})
    cache.set("second.html", {"name": "second"})
    
    # Access first to make it most recently used
    cache.get("first.html")
    
    # Add third, should evict second (least recently used)
    cache.set("third.html", {"name": "third"})
    
    # First should still be present
    if cache.get("first.html") is None:
        raise AssertionError("first.html should be in cache")
    
    # Second should be evicted
    if cache.get("second.html") is not None:
        raise AssertionError("second.html should have been evicted")
    
    return


def test_get_with_auto_reload_returns_fresh_template():
    """
        Test that get() returns template when mtime matches in auto_reload mode.
    """
    cache = TemplateCache(auto_reload=True)
    template = {"compiled": True}
    mtime = 1234567890.0
    
    cache.set("index.html", template, mtime=mtime)
    
    # Same mtime should return template
    result = cache.get("index.html", mtime=mtime)
    
    if result != template:
        raise AssertionError(f"Expected {template}, got {result}")
    
    return


def test_get_with_auto_reload_returns_none_for_stale_template():
    """
        Test that get() returns None for stale template in auto_reload mode.
    """
    cache = TemplateCache(auto_reload=True)
    template = {"compiled": True}
    old_mtime = 1234567890.0
    new_mtime = 1234567891.0
    
    cache.set("index.html", template, mtime=old_mtime)
    
    # Newer mtime should return None (stale)
    result = cache.get("index.html", mtime=new_mtime)
    
    if result is not None:
        raise AssertionError(f"Expected None for stale template, got {result}")
    
    return


def test_get_with_auto_reload_removes_stale_entry():
    """
        Test that get() removes stale entry from cache in auto_reload mode.
    """
    cache = TemplateCache(auto_reload=True)
    template = {"compiled": True}
    old_mtime = 1234567890.0
    new_mtime = 1234567891.0
    
    cache.set("index.html", template, mtime=old_mtime)
    
    if cache.size != 1:
        raise AssertionError(f"Expected size 1, got {cache.size}")
    
    # Access with newer mtime
    cache.get("index.html", mtime=new_mtime)
    
    # Entry should be removed
    if cache.size != 0:
        raise AssertionError(f"Expected size 0 after stale access, got {cache.size}")
    
    return


def test_get_without_mtime_ignores_staleness_check():
    """
        Test that get() without mtime ignores staleness check in auto_reload mode.
    """
    cache = TemplateCache(auto_reload=True)
    template = {"compiled": True}
    mtime = 1234567890.0
    
    cache.set("index.html", template, mtime=mtime)
    
    # Get without mtime should return template
    result = cache.get("index.html")
    
    if result != template:
        raise AssertionError(f"Expected {template}, got {result}")
    
    return


def test_get_with_auto_reload_disabled_ignores_mtime():
    """
        Test that get() ignores mtime when auto_reload is disabled.
    """
    cache = TemplateCache(auto_reload=False)
    template = {"compiled": True}
    old_mtime = 1234567890.0
    new_mtime = 1234567891.0
    
    cache.set("index.html", template, mtime=old_mtime)
    
    # Even with newer mtime, should return template
    result = cache.get("index.html", mtime=new_mtime)
    
    if result != template:
        raise AssertionError(f"Expected {template}, got {result}")
    
    return


def test_get_with_auto_reload_and_no_cached_mtime():
    """
        Test that get() returns None when cached entry has no mtime in auto_reload mode.
    """
    cache = TemplateCache(auto_reload=True)
    template = {"compiled": True}
    
    # Set without mtime
    cache.set("index.html", template)
    
    # Get with mtime should return None (no cached mtime to compare)
    result = cache.get("index.html", mtime=1234567890.0)
    
    if result is not None:
        raise AssertionError(f"Expected None when cached entry has no mtime, got {result}")
    
    return


# =============================================================================
# clear() Method Tests
# =============================================================================

def test_clear_removes_all_entries():
    """
        Test that clear() removes all cached entries.
    """
    cache = TemplateCache()
    
    cache.set("index.html", {"name": "index"})
    cache.set("about.html", {"name": "about"})
    cache.set("contact.html", {"name": "contact"})
    
    if cache.size != 3:
        raise AssertionError(f"Expected size 3, got {cache.size}")
    
    cache.clear()
    
    if cache.size != 0:
        raise AssertionError(f"Expected size 0 after clear, got {cache.size}")
    
    return


def test_clear_on_empty_cache():
    """
        Test that clear() works on empty cache.
    """
    cache = TemplateCache()
    
    # Should not raise
    cache.clear()
    
    if cache.size != 0:
        raise AssertionError(f"Expected size 0, got {cache.size}")
    
    return


def test_clear_allows_new_entries():
    """
        Test that clear() allows new entries to be added.
    """
    cache = TemplateCache()
    
    cache.set("old.html", {"name": "old"})
    cache.clear()
    cache.set("new.html", {"name": "new"})
    
    if cache.size != 1:
        raise AssertionError(f"Expected size 1, got {cache.size}")
    
    result = cache.get("new.html")
    if result != {"name": "new"}:
        raise AssertionError(f"Expected {{'name': 'new'}}, got {result}")
    
    return


# =============================================================================
# remove() Method Tests
# =============================================================================

def test_remove_deletes_specific_entry():
    """
        Test that remove() deletes a specific cache entry.
    """
    cache = TemplateCache()
    
    cache.set("index.html", {"name": "index"})
    cache.set("about.html", {"name": "about"})
    
    cache.remove("index.html")
    
    if cache.size != 1:
        raise AssertionError(f"Expected size 1, got {cache.size}")
    
    if cache.get("index.html") is not None:
        raise AssertionError("index.html should be removed")
    
    if cache.get("about.html") is None:
        raise AssertionError("about.html should still be in cache")
    
    return


def test_remove_nonexistent_key_does_nothing():
    """
        Test that remove() does nothing for nonexistent key.
    """
    cache = TemplateCache()
    
    cache.set("index.html", {"name": "index"})
    
    # Should not raise
    cache.remove("missing.html")
    
    if cache.size != 1:
        raise AssertionError(f"Expected size 1, got {cache.size}")
    
    return


def test_remove_on_empty_cache():
    """
        Test that remove() works on empty cache.
    """
    cache = TemplateCache()
    
    # Should not raise
    cache.remove("missing.html")
    
    if cache.size != 0:
        raise AssertionError(f"Expected size 0, got {cache.size}")
    
    return


# =============================================================================
# size Property Tests
# =============================================================================

def test_size_returns_zero_for_empty_cache():
    """
        Test that size returns 0 for empty cache.
    """
    cache = TemplateCache()
    
    if cache.size != 0:
        raise AssertionError(f"Expected size 0, got {cache.size}")
    
    return


def test_size_reflects_number_of_entries():
    """
        Test that size reflects the number of cached entries.
    """
    cache = TemplateCache()
    
    cache.set("one.html", {"n": 1})
    if cache.size != 1:
        raise AssertionError(f"Expected size 1, got {cache.size}")
    
    cache.set("two.html", {"n": 2})
    if cache.size != 2:
        raise AssertionError(f"Expected size 2, got {cache.size}")
    
    cache.set("three.html", {"n": 3})
    if cache.size != 3:
        raise AssertionError(f"Expected size 3, got {cache.size}")
    
    return


def test_size_decreases_after_remove():
    """
        Test that size decreases after remove().
    """
    cache = TemplateCache()
    
    cache.set("index.html", {"name": "index"})
    cache.set("about.html", {"name": "about"})
    
    cache.remove("index.html")
    
    if cache.size != 1:
        raise AssertionError(f"Expected size 1, got {cache.size}")
    
    return


def test_size_is_zero_after_clear():
    """
        Test that size is 0 after clear().
    """
    cache = TemplateCache()
    
    cache.set("index.html", {"name": "index"})
    cache.set("about.html", {"name": "about"})
    
    cache.clear()
    
    if cache.size != 0:
        raise AssertionError(f"Expected size 0, got {cache.size}")
    
    return


# =============================================================================
# LRU Eviction Tests
# =============================================================================

def test_lru_eviction_order():
    """
        Test that LRU eviction follows access order.
    """
    cache = TemplateCache(max_size=3)
    
    cache.set("a.html", {"name": "a"})
    cache.set("b.html", {"name": "b"})
    cache.set("c.html", {"name": "c"})
    
    # Access a and b to make them more recently used
    cache.get("a.html")
    cache.get("b.html")
    
    # Add d, should evict c (least recently used)
    cache.set("d.html", {"name": "d"})
    
    if cache.get("c.html") is not None:
        raise AssertionError("c.html should have been evicted")
    
    if cache.get("a.html") is None:
        raise AssertionError("a.html should be in cache")
    
    if cache.get("b.html") is None:
        raise AssertionError("b.html should be in cache")
    
    if cache.get("d.html") is None:
        raise AssertionError("d.html should be in cache")
    
    return


def test_lru_eviction_with_max_size_one():
    """
        Test LRU eviction with max_size=1.
    """
    cache = TemplateCache(max_size=1)
    
    cache.set("first.html", {"name": "first"})
    
    if cache.size != 1:
        raise AssertionError(f"Expected size 1, got {cache.size}")
    
    cache.set("second.html", {"name": "second"})
    
    if cache.size != 1:
        raise AssertionError(f"Expected size 1, got {cache.size}")
    
    if cache.get("first.html") is not None:
        raise AssertionError("first.html should have been evicted")
    
    if cache.get("second.html") is None:
        raise AssertionError("second.html should be in cache")
    
    return


def test_set_existing_key_updates_lru_order():
    """
        Test that set() with existing key updates LRU order.
    """
    cache = TemplateCache(max_size=2)
    
    cache.set("a.html", {"version": 1})
    cache.set("b.html", {"version": 1})
    
    # Update a, making it most recently used
    cache.set("a.html", {"version": 2})
    
    # Add c, should evict b (least recently used)
    cache.set("c.html", {"version": 1})
    
    if cache.get("b.html") is not None:
        raise AssertionError("b.html should have been evicted")
    
    if cache.get("a.html") is None:
        raise AssertionError("a.html should be in cache")
    
    return


# =============================================================================
# Edge Cases
# =============================================================================

def test_cache_with_none_template():
    """
        Test that cache can store None as a template value.
    """
    cache = TemplateCache()
    
    cache.set("null.html", None)
    
    if cache.size != 1:
        raise AssertionError(f"Expected size 1, got {cache.size}")
    
    result = cache.get("null.html")
    if result is not None:
        raise AssertionError(f"Expected None, got {result}")
    
    return


def test_cache_with_empty_string_key():
    """
        Test that cache can use empty string as key.
    """
    cache = TemplateCache()
    
    cache.set("", {"name": "empty"})
    
    if cache.size != 1:
        raise AssertionError(f"Expected size 1, got {cache.size}")
    
    result = cache.get("")
    if result != {"name": "empty"}:
        raise AssertionError(f"Expected {{'name': 'empty'}}, got {result}")
    
    return


def test_cache_with_complex_template_object():
    """
        Test that cache can store complex template objects.
    """
    cache = TemplateCache()
    
    class MockTemplate:
        def __init__(self, name):
            self.name = name
        
        def render(self, context):
            return f"Rendered {self.name}"
    
    template = MockTemplate("test")
    cache.set("complex.html", template)
    
    result = cache.get("complex.html")
    
    if result is not template:
        raise AssertionError("Should return same template object")
    
    if result.render({}) != "Rendered test":
        raise AssertionError("Template should be functional")
    
    return


def test_cache_preserves_template_identity():
    """
        Test that cache preserves template object identity.
    """
    cache = TemplateCache()
    
    template = {"compiled": True, "data": [1, 2, 3]}
    cache.set("index.html", template)
    
    result = cache.get("index.html")
    
    if result is not template:
        raise AssertionError("Should return same object (identity)")
    
    return


def test_cache_with_special_characters_in_key():
    """
        Test that cache handles special characters in keys.
    """
    cache = TemplateCache()
    
    cache.set("path/to/template.html", {"name": "nested"})
    cache.set("template-with-dashes.html", {"name": "dashes"})
    cache.set("template_with_underscores.html", {"name": "underscores"})
    
    if cache.size != 3:
        raise AssertionError(f"Expected size 3, got {cache.size}")
    
    if cache.get("path/to/template.html") is None:
        raise AssertionError("Should find nested path key")
    
    if cache.get("template-with-dashes.html") is None:
        raise AssertionError("Should find dashes key")
    
    if cache.get("template_with_underscores.html") is None:
        raise AssertionError("Should find underscores key")
    
    return


def test_auto_reload_with_older_mtime():
    """
        Test that auto_reload returns template when provided mtime is older.
    """
    cache = TemplateCache(auto_reload=True)
    template = {"compiled": True}
    cached_mtime = 1234567891.0
    older_mtime = 1234567890.0
    
    cache.set("index.html", template, mtime=cached_mtime)
    
    # Older mtime should still return template (not stale)
    result = cache.get("index.html", mtime=older_mtime)
    
    if result != template:
        raise AssertionError(f"Expected {template}, got {result}")
    
    return


def test_auto_reload_with_equal_mtime():
    """
        Test that auto_reload returns template when mtime is equal.
    """
    cache = TemplateCache(auto_reload=True)
    template = {"compiled": True}
    mtime = 1234567890.0
    
    cache.set("index.html", template, mtime=mtime)
    
    # Equal mtime should return template
    result = cache.get("index.html", mtime=mtime)
    
    if result != template:
        raise AssertionError(f"Expected {template}, got {result}")
    
    return


# =============================================================================
# Property Tests
# =============================================================================

def test_max_size_property():
    """
        Test that max_size property returns configured value.
    """
    cache = TemplateCache(max_size=250)
    
    if cache.max_size != 250:
        raise AssertionError(f"Expected max_size 250, got {cache.max_size}")
    
    return


def test_auto_reload_property():
    """
        Test that auto_reload property returns configured value.
    """
    cache_enabled = TemplateCache(auto_reload=True)
    cache_disabled = TemplateCache(auto_reload=False)
    
    if cache_enabled.auto_reload is not True:
        raise AssertionError("Expected auto_reload True")
    
    if cache_disabled.auto_reload is not False:
        raise AssertionError("Expected auto_reload False")
    
    return



# =============================================================================
# Property-Based Tests
# =============================================================================

import random
import string


def _generate_random_template_name(length: int = 12) -> str:
    """
        Generate a random template name for property testing.

        :param length: Length of the random name (excluding extension).

        :returns: Random template name string with .html extension.
    """
    chars = string.ascii_lowercase + string.digits + "_-"
    name = "".join(random.choice(chars) for _ in range(length))
    return f"{name}.html"


def _generate_random_mtime() -> float:
    """
        Generate a random modification time for property testing.

        Generates timestamps in a realistic range (year 2020 to 2030).

        :returns: Random modification time as a float.
    """
    # Timestamps between 2020-01-01 and 2030-01-01
    min_time = 1577836800.0  # 2020-01-01 00:00:00 UTC
    max_time = 1893456000.0  # 2030-01-01 00:00:00 UTC
    return random.uniform(min_time, max_time)


def _generate_increasing_mtimes(count: int, base_mtime: float) -> list:
    """
        Generate a list of strictly increasing modification times.

        :param count: Number of mtimes to generate.
        :param base_mtime: Starting mtime value.

        :returns: List of strictly increasing mtime values.
    """
    mtimes = []
    current = base_mtime
    for _ in range(count):
        # Add a random increment between 0.001 and 100 seconds
        increment = random.uniform(0.001, 100.0)
        current += increment
        mtimes.append(current)
    return mtimes


def test_property_cache_consistency_stale_detection():
    """
        Property test for cache consistency with stale detection.

        **Property 7: Cache Consistency**

        *For any* cached template, when auto_reload is enabled and the
        template file is modified (mtime increases), subsequent renders
        SHALL use the updated template content.

        **Validates: Requirements 6.6, 6.8**

        This property test verifies that:
        1. When auto_reload is enabled and a template's mtime increases,
           the cache returns None (indicating staleness)
        2. This holds for any sequence of cache operations with varying mtimes
        3. The cache correctly distinguishes between fresh and stale entries

        Test strategy:
        - Generate random template names and mtimes
        - Cache templates with initial mtimes
        - Access with newer mtimes and verify None is returned
        - Verify the stale entry is removed from cache
    """
    iterations = 100

    for iteration in range(iterations):
        # Create a fresh cache with auto_reload enabled
        cache = TemplateCache(max_size=100, auto_reload=True)

        # Generate random template name and initial mtime
        template_name = _generate_random_template_name()
        initial_mtime = _generate_random_mtime()

        # Create a mock template object
        template = {"name": template_name, "iteration": iteration}

        # Cache the template with initial mtime
        cache.set(template_name, template, mtime=initial_mtime)

        # Verify template is cached
        if cache.size != 1:
            raise AssertionError(
                f"Iteration {iteration}: Expected cache size 1, got {cache.size}"
            )

        # Generate a newer mtime (simulating file modification)
        newer_mtime = initial_mtime + random.uniform(0.001, 1000.0)

        # Access with newer mtime - should return None (stale)
        result = cache.get(template_name, mtime=newer_mtime)

        if result is not None:
            raise AssertionError(
                f"Iteration {iteration}: Cache should return None for stale "
                f"template. Initial mtime: {initial_mtime}, newer mtime: "
                f"{newer_mtime}, but got: {result}"
            )

        # Verify stale entry was removed from cache
        if cache.size != 0:
            raise AssertionError(
                f"Iteration {iteration}: Stale entry should be removed from "
                f"cache. Expected size 0, got {cache.size}"
            )

    return


def test_property_cache_consistency_fresh_entries():
    """
        Property test for cache consistency with fresh entries.

        **Property 7: Cache Consistency** (fresh entries)

        *For any* cached template, when auto_reload is enabled and the
        template file has NOT been modified (mtime unchanged or older),
        the cache SHALL return the cached template.

        **Validates: Requirements 6.6, 6.8**

        This property test verifies that:
        1. When mtime is equal to cached mtime, template is returned
        2. When mtime is older than cached mtime, template is returned
        3. Fresh entries remain in cache after access

        Test strategy:
        - Generate random template names and mtimes
        - Cache templates with mtimes
        - Access with same or older mtimes and verify template is returned
        - Verify entry remains in cache
    """
    iterations = 100

    for iteration in range(iterations):
        # Create a fresh cache with auto_reload enabled
        cache = TemplateCache(max_size=100, auto_reload=True)

        # Generate random template name and mtime
        template_name = _generate_random_template_name()
        cached_mtime = _generate_random_mtime()

        # Create a mock template object
        template = {"name": template_name, "iteration": iteration}

        # Cache the template
        cache.set(template_name, template, mtime=cached_mtime)

        # Test 1: Access with same mtime - should return template
        result = cache.get(template_name, mtime=cached_mtime)

        if result != template:
            raise AssertionError(
                f"Iteration {iteration}: Cache should return template when "
                f"mtime is equal. Expected {template}, got {result}"
            )

        # Verify entry remains in cache
        if cache.size != 1:
            raise AssertionError(
                f"Iteration {iteration}: Entry should remain in cache after "
                f"fresh access. Expected size 1, got {cache.size}"
            )

        # Test 2: Access with older mtime - should return template
        older_mtime = cached_mtime - random.uniform(0.001, 1000.0)
        result = cache.get(template_name, mtime=older_mtime)

        if result != template:
            raise AssertionError(
                f"Iteration {iteration}: Cache should return template when "
                f"mtime is older. Cached mtime: {cached_mtime}, older mtime: "
                f"{older_mtime}, but got: {result}"
            )

        # Verify entry still remains in cache
        if cache.size != 1:
            raise AssertionError(
                f"Iteration {iteration}: Entry should remain in cache after "
                f"access with older mtime. Expected size 1, got {cache.size}"
            )

    return


def test_property_cache_consistency_multiple_templates():
    """
        Property test for cache consistency with multiple templates.

        **Property 7: Cache Consistency** (multiple templates)

        *For any* set of cached templates, when auto_reload is enabled,
        staleness detection SHALL work independently for each template.

        **Validates: Requirements 6.6, 6.8**

        This property test verifies that:
        1. Multiple templates can be cached with different mtimes
        2. Staleness detection works independently for each template
        3. Stale templates are removed without affecting fresh templates

        Test strategy:
        - Cache multiple templates with different mtimes
        - Mark some as stale by accessing with newer mtimes
        - Verify only stale templates are removed
        - Verify fresh templates remain accessible
    """
    iterations = 100

    for iteration in range(iterations):
        # Create a fresh cache with auto_reload enabled
        cache = TemplateCache(max_size=100, auto_reload=True)

        # Generate 3-10 random templates
        num_templates = random.randint(3, 10)
        templates = []

        for i in range(num_templates):
            template_name = _generate_random_template_name()
            mtime = _generate_random_mtime()
            template = {"name": template_name, "index": i}

            cache.set(template_name, template, mtime=mtime)
            templates.append({
                "name": template_name,
                "mtime": mtime,
                "template": template
            })

        # Verify all templates are cached
        if cache.size != num_templates:
            raise AssertionError(
                f"Iteration {iteration}: Expected cache size {num_templates}, "
                f"got {cache.size}"
            )

        # Randomly select some templates to mark as stale
        num_stale = random.randint(1, num_templates - 1)
        stale_indices = random.sample(range(num_templates), num_stale)

        # Access stale templates with newer mtimes
        for idx in stale_indices:
            t = templates[idx]
            newer_mtime = t["mtime"] + random.uniform(0.001, 1000.0)
            result = cache.get(t["name"], mtime=newer_mtime)

            if result is not None:
                raise AssertionError(
                    f"Iteration {iteration}: Template at index {idx} should be "
                    f"stale. Got: {result}"
                )

        # Verify cache size decreased by number of stale templates
        expected_size = num_templates - num_stale
        if cache.size != expected_size:
            raise AssertionError(
                f"Iteration {iteration}: Expected cache size {expected_size} "
                f"after removing {num_stale} stale templates, got {cache.size}"
            )

        # Verify fresh templates are still accessible
        fresh_indices = [i for i in range(num_templates) if i not in stale_indices]
        for idx in fresh_indices:
            t = templates[idx]
            result = cache.get(t["name"], mtime=t["mtime"])

            if result != t["template"]:
                raise AssertionError(
                    f"Iteration {iteration}: Fresh template at index {idx} "
                    f"should still be accessible. Expected {t['template']}, "
                    f"got {result}"
                )

    return


def test_property_cache_consistency_sequential_modifications():
    """
        Property test for cache consistency with sequential modifications.

        **Property 7: Cache Consistency** (sequential modifications)

        *For any* sequence of template modifications (increasing mtimes),
        the cache SHALL correctly detect staleness at each step.

        **Validates: Requirements 6.6, 6.8**

        This property test verifies that:
        1. A template can be cached, marked stale, re-cached, and marked
           stale again in sequence
        2. Each modification is correctly detected
        3. The cache state is consistent after each operation

        Test strategy:
        - Generate a sequence of increasing mtimes
        - Cache template, access with newer mtime (stale), re-cache, repeat
        - Verify correct behavior at each step
    """
    iterations = 100

    for iteration in range(iterations):
        # Create a fresh cache with auto_reload enabled
        cache = TemplateCache(max_size=100, auto_reload=True)

        template_name = _generate_random_template_name()
        base_mtime = _generate_random_mtime()

        # Generate 3-8 sequential modifications
        num_modifications = random.randint(3, 8)
        mtimes = _generate_increasing_mtimes(num_modifications, base_mtime)

        for mod_idx in range(num_modifications):
            current_mtime = mtimes[mod_idx]
            template = {"name": template_name, "version": mod_idx}

            # Cache the template with current mtime
            cache.set(template_name, template, mtime=current_mtime)

            # Verify template is cached
            if cache.size != 1:
                raise AssertionError(
                    f"Iteration {iteration}, mod {mod_idx}: Expected cache "
                    f"size 1, got {cache.size}"
                )

            # Access with same mtime - should return template
            result = cache.get(template_name, mtime=current_mtime)
            if result != template:
                raise AssertionError(
                    f"Iteration {iteration}, mod {mod_idx}: Cache should "
                    f"return template with same mtime. Expected {template}, "
                    f"got {result}"
                )

            # If not the last modification, simulate file change
            if mod_idx < num_modifications - 1:
                next_mtime = mtimes[mod_idx + 1]

                # Access with newer mtime - should return None (stale)
                result = cache.get(template_name, mtime=next_mtime)

                if result is not None:
                    raise AssertionError(
                        f"Iteration {iteration}, mod {mod_idx}: Cache should "
                        f"return None for stale template. Current mtime: "
                        f"{current_mtime}, next mtime: {next_mtime}, "
                        f"got: {result}"
                    )

                # Verify stale entry was removed
                if cache.size != 0:
                    raise AssertionError(
                        f"Iteration {iteration}, mod {mod_idx}: Stale entry "
                        f"should be removed. Expected size 0, got {cache.size}"
                    )

    return


def test_property_cache_consistency_auto_reload_disabled():
    """
        Property test for cache behavior when auto_reload is disabled.

        **Property 7: Cache Consistency** (auto_reload disabled)

        *For any* cached template, when auto_reload is disabled, the cache
        SHALL return the cached template regardless of mtime changes.

        **Validates: Requirements 6.6, 6.8**

        This property test verifies that:
        1. When auto_reload is False, mtime is ignored
        2. Templates are returned even when mtime indicates staleness
        3. Cache entries are not removed based on mtime

        Test strategy:
        - Create cache with auto_reload=False
        - Cache templates with mtimes
        - Access with newer mtimes and verify template is still returned
        - Verify entries remain in cache
    """
    iterations = 100

    for iteration in range(iterations):
        # Create a cache with auto_reload DISABLED
        cache = TemplateCache(max_size=100, auto_reload=False)

        template_name = _generate_random_template_name()
        cached_mtime = _generate_random_mtime()
        template = {"name": template_name, "iteration": iteration}

        # Cache the template
        cache.set(template_name, template, mtime=cached_mtime)

        # Generate a much newer mtime
        newer_mtime = cached_mtime + random.uniform(1000.0, 10000.0)

        # Access with newer mtime - should STILL return template
        # (auto_reload is disabled, so mtime is ignored)
        result = cache.get(template_name, mtime=newer_mtime)

        if result != template:
            raise AssertionError(
                f"Iteration {iteration}: With auto_reload=False, cache should "
                f"return template regardless of mtime. Cached mtime: "
                f"{cached_mtime}, newer mtime: {newer_mtime}, expected "
                f"{template}, got {result}"
            )

        # Verify entry remains in cache
        if cache.size != 1:
            raise AssertionError(
                f"Iteration {iteration}: Entry should remain in cache when "
                f"auto_reload is disabled. Expected size 1, got {cache.size}"
            )

    return


def test_property_cache_consistency_no_mtime_provided():
    """
        Property test for cache behavior when no mtime is provided on get.

        **Property 7: Cache Consistency** (no mtime on get)

        *For any* cached template, when get() is called without an mtime
        parameter, the cache SHALL return the cached template without
        staleness checking.

        **Validates: Requirements 6.6, 6.8**

        This property test verifies that:
        1. When get() is called without mtime, staleness is not checked
        2. Templates are returned regardless of cached mtime
        3. This works even when auto_reload is enabled

        Test strategy:
        - Create cache with auto_reload=True
        - Cache templates with mtimes
        - Access without mtime parameter and verify template is returned
    """
    iterations = 100

    for iteration in range(iterations):
        # Create a cache with auto_reload enabled
        cache = TemplateCache(max_size=100, auto_reload=True)

        template_name = _generate_random_template_name()
        cached_mtime = _generate_random_mtime()
        template = {"name": template_name, "iteration": iteration}

        # Cache the template with mtime
        cache.set(template_name, template, mtime=cached_mtime)

        # Access WITHOUT mtime parameter - should return template
        result = cache.get(template_name)

        if result != template:
            raise AssertionError(
                f"Iteration {iteration}: When get() is called without mtime, "
                f"cache should return template. Expected {template}, got {result}"
            )

        # Verify entry remains in cache
        if cache.size != 1:
            raise AssertionError(
                f"Iteration {iteration}: Entry should remain in cache when "
                f"get() is called without mtime. Expected size 1, got {cache.size}"
            )

    return


def test_property_cache_consistency_no_cached_mtime():
    """
        Property test for cache behavior when template was cached without mtime.

        **Property 7: Cache Consistency** (no cached mtime)

        *For any* template cached without an mtime, when auto_reload is
        enabled and get() is called with an mtime, the cache SHALL return
        None (treating the entry as stale since it cannot verify freshness).

        **Validates: Requirements 6.6, 6.8**

        This property test verifies that:
        1. Templates cached without mtime are treated as stale when
           get() is called with an mtime (in auto_reload mode)
        2. This is a conservative approach to ensure freshness

        Test strategy:
        - Create cache with auto_reload=True
        - Cache templates WITHOUT mtime
        - Access WITH mtime parameter and verify None is returned
    """
    iterations = 100

    for iteration in range(iterations):
        # Create a cache with auto_reload enabled
        cache = TemplateCache(max_size=100, auto_reload=True)

        template_name = _generate_random_template_name()
        template = {"name": template_name, "iteration": iteration}

        # Cache the template WITHOUT mtime
        cache.set(template_name, template)

        # Access WITH mtime parameter - should return None
        # (no cached mtime to compare, so treated as stale)
        query_mtime = _generate_random_mtime()
        result = cache.get(template_name, mtime=query_mtime)

        if result is not None:
            raise AssertionError(
                f"Iteration {iteration}: When template has no cached mtime "
                f"and get() is called with mtime, cache should return None. "
                f"Got: {result}"
            )

        # Verify stale entry was removed
        if cache.size != 0:
            raise AssertionError(
                f"Iteration {iteration}: Entry without mtime should be "
                f"removed when accessed with mtime. Expected size 0, "
                f"got {cache.size}"
            )

    return

