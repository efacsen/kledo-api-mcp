"""
Tests for Kledo cache module
"""
import pytest
import time
from src.cache import KledoCache, CacheEntry


class TestCacheEntry:
    """Test suite for CacheEntry class."""

    def test_init(self):
        """Test cache entry initialization."""
        value = {"test": "data"}
        ttl = 3600
        entry = CacheEntry(value, ttl)

        assert entry.value == value
        assert entry.ttl == ttl
        assert entry.hits == 0
        assert entry.created_at > 0
        assert entry.last_accessed == entry.created_at

    def test_is_expired_fresh(self):
        """Test is_expired returns False for fresh entry."""
        entry = CacheEntry("test", ttl=3600)
        assert not entry.is_expired

    def test_is_expired_old(self):
        """Test is_expired returns True for expired entry."""
        entry = CacheEntry("test", ttl=1)
        time.sleep(1.1)
        assert entry.is_expired

    def test_access(self):
        """Test accessing cache entry updates stats."""
        entry = CacheEntry("test_value", ttl=3600)
        initial_hits = entry.hits
        initial_accessed = entry.last_accessed

        time.sleep(0.1)
        value = entry.access()

        assert value == "test_value"
        assert entry.hits == initial_hits + 1
        assert entry.last_accessed > initial_accessed

    def test_age(self):
        """Test age calculation."""
        entry = CacheEntry("test", ttl=3600)
        time.sleep(0.1)
        assert entry.age >= 0.1


class TestKledoCache:
    """Test suite for KledoCache class."""

    def test_init_default(self):
        """Test cache initialization with defaults."""
        cache = KledoCache()

        assert cache._enabled is True
        assert len(cache._cache) == 0
        assert cache._max_size == 1000

    def test_init_disabled(self):
        """Test cache initialization when disabled."""
        cache = KledoCache(enabled=False)

        assert cache._enabled is False

    def test_init_with_config(self, sample_cache_config):
        """Test cache initialization with config file."""
        cache = KledoCache(config_path=sample_cache_config)

        assert cache._ttl_config["products"] == 7200
        assert cache._ttl_config["invoices"] == 1800
        assert cache._ttl_config["reports"] == 3600

    def test_set_and_get(self):
        """Test setting and getting cache values."""
        cache = KledoCache()

        cache.set("test_key", "test_value", category="default")
        value = cache.get("test_key")

        assert value == "test_value"
        assert cache._stats["sets"] == 1
        assert cache._stats["hits"] == 1

    def test_get_nonexistent_key(self):
        """Test getting non-existent key returns None."""
        cache = KledoCache()

        value = cache.get("nonexistent")

        assert value is None
        assert cache._stats["misses"] == 1

    def test_get_expired_entry(self):
        """Test getting expired entry returns None."""
        cache = KledoCache()

        cache.set("test_key", "test_value", ttl=1)
        time.sleep(1.1)
        value = cache.get("test_key")

        assert value is None
        assert cache._stats["expirations"] >= 1

    def test_set_with_explicit_ttl(self):
        """Test setting value with explicit TTL."""
        cache = KledoCache()

        cache.set("test_key", "test_value", ttl=3600)

        assert "test_key" in cache._cache
        assert cache._cache["test_key"].ttl == 3600

    def test_set_with_category_ttl(self, sample_cache_config):
        """Test setting value with category-based TTL."""
        cache = KledoCache(config_path=sample_cache_config)

        cache.set("test_key", "test_value", category="products")

        assert cache._cache["test_key"].ttl == 7200

    def test_cache_disabled_get(self):
        """Test that get returns None when cache disabled."""
        cache = KledoCache(enabled=False)

        cache._cache["test_key"] = CacheEntry("test_value", 3600)
        value = cache.get("test_key")

        assert value is None

    def test_cache_disabled_set(self):
        """Test that set does nothing when cache disabled."""
        cache = KledoCache(enabled=False)

        cache.set("test_key", "test_value")

        assert len(cache._cache) == 0

    def test_delete(self):
        """Test deleting cache entry."""
        cache = KledoCache()

        cache.set("test_key", "test_value")
        assert cache.get("test_key") is not None

        result = cache.delete("test_key")

        assert result is True
        assert cache.get("test_key") is None

    def test_delete_nonexistent(self):
        """Test deleting non-existent key."""
        cache = KledoCache()

        result = cache.delete("nonexistent")

        assert result is False

    def test_clear(self):
        """Test clearing all cache entries."""
        cache = KledoCache()

        cache.set("key1", "value1")
        cache.set("key2", "value2")
        cache.set("key3", "value3")

        count = cache.clear()

        assert count == 3
        assert len(cache._cache) == 0

    def test_eviction_when_full(self):
        """Test that oldest entry is evicted when cache is full."""
        cache = KledoCache()
        cache._max_size = 3

        cache.set("key1", "value1")
        time.sleep(0.1)
        cache.set("key2", "value2")
        time.sleep(0.1)
        cache.set("key3", "value3")
        time.sleep(0.1)

        # This should evict key1 (oldest)
        cache.set("key4", "value4")

        assert cache.get("key1") is None
        assert cache.get("key2") is not None
        assert cache.get("key3") is not None
        assert cache.get("key4") is not None
        assert cache._stats["evictions"] == 1

    def test_cleanup_expired(self):
        """Test cleanup of expired entries."""
        cache = KledoCache()
        cache._cleanup_interval = 0  # Force cleanup on every get

        cache.set("key1", "value1", ttl=1)
        cache.set("key2", "value2", ttl=3600)

        time.sleep(1.1)

        # This should trigger cleanup
        cache.get("key2")

        assert "key1" not in cache._cache
        assert "key2" in cache._cache

    def test_get_stats(self):
        """Test getting cache statistics."""
        cache = KledoCache()

        cache.set("key1", "value1")
        cache.get("key1")  # hit
        cache.get("key2")  # miss

        stats = cache.get_stats()

        assert stats["enabled"] is True
        assert stats["size"] == 1
        assert stats["hits"] == 1
        assert stats["misses"] == 1
        assert stats["sets"] == 1
        assert stats["total_requests"] == 2
        assert "50.00" in stats["hit_rate"]

    def test_get_stats_no_requests(self):
        """Test stats with no requests."""
        cache = KledoCache()

        stats = cache.get_stats()

        assert stats["total_requests"] == 0
        assert stats["hit_rate"] == "0.00%"

    def test_get_keys(self):
        """Test getting all cache keys."""
        cache = KledoCache()

        cache.set("key1", "value1")
        cache.set("key2", "value2")

        keys = cache.get_keys()

        assert len(keys) == 2
        assert "key1" in keys
        assert "key2" in keys

    def test_get_entry_info(self):
        """Test getting entry information."""
        cache = KledoCache()

        cache.set("test_key", "test_value", ttl=3600)

        info = cache.get_entry_info("test_key")

        assert info is not None
        assert info["ttl"] == 3600
        assert info["hits"] == 0
        assert info["is_expired"] is False
        assert "created_at" in info
        assert "last_accessed" in info

    def test_get_entry_info_nonexistent(self):
        """Test getting info for non-existent entry."""
        cache = KledoCache()

        info = cache.get_entry_info("nonexistent")

        assert info is None

    def test_multiple_accesses_update_hits(self):
        """Test that multiple accesses update hit counter."""
        cache = KledoCache()

        cache.set("test_key", "test_value")

        cache.get("test_key")
        cache.get("test_key")
        cache.get("test_key")

        entry = cache._cache["test_key"]
        assert entry.hits == 3

    def test_lru_eviction_based_on_access(self):
        """Test LRU eviction based on access time."""
        cache = KledoCache()
        cache._max_size = 3

        cache.set("key1", "value1")
        time.sleep(0.1)
        cache.set("key2", "value2")
        time.sleep(0.1)
        cache.set("key3", "value3")
        time.sleep(0.1)

        # Access key1 to make it more recent
        cache.get("key1")
        time.sleep(0.1)

        # This should evict key2 (least recently accessed)
        cache.set("key4", "value4")

        assert cache.get("key1") is not None
        assert cache.get("key2") is None
        assert cache.get("key3") is not None
        assert cache.get("key4") is not None
