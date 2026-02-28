"""
    Template cache module.
    
    This module provides the TemplateCache class for caching compiled
    templates in memory. The cache supports configurable size limits
    and automatic invalidation when templates change (auto_reload mode).
    
    The cache uses an LRU (Least Recently Used) eviction policy when
    the maximum size is reached. In auto_reload mode, cached templates
    are invalidated when their modification time changes.
    
    Example:
        cache = TemplateCache(max_size=400, auto_reload=False)
        
        # Cache a compiled template
        cache.set("index.html", compiled_template, mtime=1234567890.0)
        
        # Retrieve from cache
        template = cache.get("index.html")
        
        # Check with staleness detection
        template = cache.get("index.html", mtime=1234567891.0)  # Returns None if stale
        
        # Clear specific template
        cache.remove("index.html")
        
        # Clear all templates
        cache.clear()
"""

from collections import OrderedDict
from typing import Any, Optional


class CacheEntry:
    """
        Represents a cached template entry.
        
        Stores the compiled template along with its modification time
        for staleness detection in auto_reload mode.
        
        :ivar template: The compiled template object.
        :ivar mtime: The modification time when the template was cached.
    """
    
    def __init__(
        self,
        template: Any,
        mtime: Optional[float] = None
    ):
        """
            Construct a cache entry.
            
            :param template: The compiled template object.
            :param mtime: The modification time for staleness tracking.
        """
        self.template = template
        self.mtime = mtime
        return


class TemplateCache:
    """
        Caches compiled templates for performance.
        
        The cache stores compiled template objects in memory to avoid
        repeated parsing and compilation. It supports:
        
        - Configurable maximum size with LRU eviction
        - Auto-reload mode for development (checks modification times)
        - Manual cache clearing and removal
        
        In production mode (auto_reload=False), templates are cached
        indefinitely until manually cleared or evicted due to size limits.
        
        In development mode (auto_reload=True), the cache checks the
        modification time of templates and returns None for stale entries,
        allowing the caller to reload the template.
        
        :ivar _cache: OrderedDict storing cache entries (LRU order).
        :ivar _max_size: Maximum number of cached templates.
        :ivar _auto_reload: Whether to check for template changes.
        
        Example:
            cache = TemplateCache(max_size=400, auto_reload=False)
            
            # Cache a template
            cache.set("index.html", compiled_template, mtime=1234567890.0)
            
            # Get from cache
            template = cache.get("index.html")
            
            # Get with staleness check (auto_reload mode)
            template = cache.get("index.html", mtime=current_mtime)
    """
    
    def __init__(
        self,
        max_size: int = 400,
        auto_reload: bool = False
    ):
        """
            Construct a template cache.
            
            :param max_size: Maximum number of cached templates.
                            When exceeded, least recently used templates
                            are evicted. Defaults to 400.
            :param auto_reload: Check for template changes (debug mode).
                               When True, get() compares modification times
                               and returns None for stale templates.
                               Defaults to False.
            
            Example:
                # Production cache
                cache = TemplateCache(max_size=400, auto_reload=False)
                
                # Development cache with auto-reload
                cache = TemplateCache(max_size=100, auto_reload=True)
        """
        self._cache: OrderedDict[str, CacheEntry] = OrderedDict()
        self._max_size = max_size
        self._auto_reload = auto_reload
        return
    
    def get(
        self,
        key: str,
        mtime: Optional[float] = None
    ) -> Optional[Any]:
        """
            Get a cached template.
            
            Retrieves a template from the cache if it exists and is fresh.
            In auto_reload mode, the template is considered stale if the
            provided mtime is newer than the cached mtime.
            
            When a template is retrieved, it is moved to the end of the
            LRU order (most recently used).
            
            :param key: Cache key (usually template name).
            :param mtime: Current modification time for staleness check.
                         Only used when auto_reload is enabled.
            
            :returns: Cached template if found and fresh, None otherwise.
            
            Example:
                # Simple get
                template = cache.get("index.html")
                
                # Get with staleness check
                current_mtime = os.path.getmtime(template_path)
                template = cache.get("index.html", mtime=current_mtime)
                if template is None:
                    # Template not cached or stale, need to reload
                    pass
        """
        if key not in self._cache:
            return None
        
        entry = self._cache[key]
        
        # Check for staleness in auto_reload mode
        if self._auto_reload and mtime is not None:
            if entry.mtime is None or mtime > entry.mtime:
                # Template is stale, remove from cache
                del self._cache[key]
                return None
        
        # Move to end (most recently used)
        self._cache.move_to_end(key)
        
        return entry.template
    
    def set(
        self,
        key: str,
        template: Any,
        mtime: Optional[float] = None
    ) -> None:
        """
            Cache a compiled template.
            
            Stores a compiled template in the cache. If the cache is at
            maximum capacity, the least recently used template is evicted.
            
            If the key already exists, the entry is updated and moved to
            the end of the LRU order.
            
            If max_size is 0, nothing is stored (caching is disabled).
            
            :param key: Cache key (usually template name).
            :param template: Compiled template object.
            :param mtime: Modification time for staleness tracking.
                         Should be provided when auto_reload is enabled.
            
            Example:
                # Cache without mtime (production)
                cache.set("index.html", compiled_template)
                
                # Cache with mtime (development)
                mtime = os.path.getmtime(template_path)
                cache.set("index.html", compiled_template, mtime=mtime)
        """
        # If max_size is 0, caching is disabled
        if self._max_size <= 0:
            return
        
        # If key exists, remove it first (will be re-added at end)
        if key in self._cache:
            del self._cache[key]
        
        # Evict least recently used if at capacity
        while len(self._cache) >= self._max_size:
            # Remove first item (least recently used)
            self._cache.popitem(last=False)
        
        # Add new entry at end (most recently used)
        self._cache[key] = CacheEntry(template=template, mtime=mtime)
        return
    
    def clear(self) -> None:
        """
            Clear all cached templates.
            
            Removes all templates from the cache. This is useful when
            templates have been modified and need to be reloaded.
            
            Example:
                # Clear entire cache
                cache.clear()
        """
        self._cache.clear()
        return
    
    def remove(self, key: str) -> None:
        """
            Remove a specific template from cache.
            
            Removes a single template from the cache if it exists.
            Does nothing if the key is not in the cache.
            
            :param key: Cache key to remove.
            
            Example:
                # Remove specific template
                cache.remove("index.html")
        """
        if key in self._cache:
            del self._cache[key]
        return
    
    @property
    def size(self) -> int:
        """
            Return current cache size.
            
            Returns the number of templates currently in the cache.
            
            :returns: Number of cached templates.
            
            Example:
                print(f"Cache contains {cache.size} templates")
        """
        return len(self._cache)
    
    @property
    def max_size(self) -> int:
        """
            Return maximum cache size.
            
            Returns the configured maximum number of templates
            that can be stored in the cache.
            
            :returns: Maximum cache size.
            
            Example:
                print(f"Cache can hold up to {cache.max_size} templates")
        """
        return self._max_size
    
    @property
    def auto_reload(self) -> bool:
        """
            Return whether auto-reload is enabled.
            
            When auto-reload is enabled, the cache checks modification
            times and returns None for stale templates.
            
            :returns: True if auto-reload is enabled, False otherwise.
            
            Example:
                if cache.auto_reload:
                    print("Cache is in development mode")
        """
        return self._auto_reload

