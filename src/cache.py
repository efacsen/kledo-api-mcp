"""
Caching mechanism for Kledo MCP Server
"""
import time
from typing import Any, Dict, Optional, Tuple
from datetime import datetime
from loguru import logger
import yaml
from pathlib import Path


class CacheEntry:
    """Represents a single cache entry."""

    def __init__(self, value: Any, ttl: int):
        """
        Initialize cache entry.

        Args:
            value: Cached value
            ttl: Time to live in seconds
        """
        self.value = value
        self.created_at = time.time()
        self.ttl = ttl
        self.hits = 0
        self.last_accessed = self.created_at

    @property
    def is_expired(self) -> bool:
        """Check if cache entry has expired."""
        return time.time() - self.created_at > self.ttl

    def access(self) -> Any:
        """Access the cached value and update stats."""
        self.hits += 1
        self.last_accessed = time.time()
        return self.value

    @property
    def age(self) -> float:
        """Get age of cache entry in seconds."""
        return time.time() - self.created_at


class KledoCache:
    """Simple in-memory cache with TTL support."""

    def __init__(self, config_path: Optional[str] = None, enabled: bool = True):
        """
        Initialize cache.

        Args:
            config_path: Path to cache configuration YAML file
            enabled: Whether caching is enabled
        """
        self._cache: Dict[str, CacheEntry] = {}
        self._enabled = enabled
        self._ttl_config: Dict[str, int] = {}
        self._max_size = 1000
        self._cleanup_interval = 300
        self._last_cleanup = time.time()

        # Statistics
        self._stats = {
            "hits": 0,
            "misses": 0,
            "sets": 0,
            "evictions": 0,
            "expirations": 0
        }

        if config_path:
            self._load_config(config_path)

        logger.info(f"Cache initialized (enabled={enabled}, max_size={self._max_size})")

    def _load_config(self, config_path: str) -> None:
        """Load cache configuration from YAML file."""
        try:
            path = Path(config_path)
            if not path.exists():
                logger.warning(f"Cache config file not found: {config_path}")
                return

            with open(path, 'r') as f:
                config = yaml.safe_load(f)

            # Load TTL configuration
            cache_tiers = config.get("cache_tiers", {})
            for tier_name, tier_config in cache_tiers.items():
                for key, ttl in tier_config.items():
                    self._ttl_config[key] = ttl

            # Load cache settings
            settings = config.get("cache_settings", {})
            self._max_size = settings.get("max_size", self._max_size)
            self._cleanup_interval = settings.get("cleanup_interval", self._cleanup_interval)

            logger.info(f"Loaded cache configuration from {config_path}")
            logger.debug(f"TTL config: {self._ttl_config}")

        except Exception as e:
            logger.error(f"Error loading cache config: {str(e)}")

    def _get_ttl(self, category: str, default: int = 1800) -> int:
        """
        Get TTL for a category.

        Args:
            category: Cache category
            default: Default TTL if category not found

        Returns:
            TTL in seconds
        """
        return self._ttl_config.get(category, default)

    def _cleanup_expired(self) -> None:
        """Remove expired entries from cache."""
        if time.time() - self._last_cleanup < self._cleanup_interval:
            return

        expired_keys = [
            key for key, entry in self._cache.items()
            if entry.is_expired
        ]

        for key in expired_keys:
            del self._cache[key]
            self._stats["expirations"] += 1

        if expired_keys:
            logger.debug(f"Cleaned up {len(expired_keys)} expired cache entries")

        self._last_cleanup = time.time()

    def _evict_oldest(self) -> None:
        """Evict oldest entry when cache is full."""
        if not self._cache:
            return

        # Find least recently used entry
        oldest_key = min(
            self._cache.keys(),
            key=lambda k: self._cache[k].last_accessed
        )

        del self._cache[oldest_key]
        self._stats["evictions"] += 1
        logger.debug(f"Evicted cache entry: {oldest_key}")

    def get(self, key: str) -> Optional[Any]:
        """
        Get value from cache.

        Args:
            key: Cache key

        Returns:
            Cached value or None if not found/expired
        """
        if not self._enabled:
            return None

        self._cleanup_expired()

        if key in self._cache:
            entry = self._cache[key]
            if entry.is_expired:
                del self._cache[key]
                self._stats["misses"] += 1
                self._stats["expirations"] += 1
                return None

            self._stats["hits"] += 1
            return entry.access()

        self._stats["misses"] += 1
        return None

    def set(self, key: str, value: Any, category: str = "default", ttl: Optional[int] = None) -> None:
        """
        Set value in cache.

        Args:
            key: Cache key
            value: Value to cache
            category: Cache category (for TTL lookup)
            ttl: Optional explicit TTL (overrides category)
        """
        if not self._enabled:
            return

        # Use explicit TTL or lookup by category
        cache_ttl = ttl if ttl is not None else self._get_ttl(category)

        # Evict if cache is full
        if len(self._cache) >= self._max_size:
            self._evict_oldest()

        self._cache[key] = CacheEntry(value, cache_ttl)
        self._stats["sets"] += 1

    def delete(self, key: str) -> bool:
        """
        Delete entry from cache.

        Args:
            key: Cache key

        Returns:
            True if entry was deleted
        """
        if key in self._cache:
            del self._cache[key]
            return True
        return False

    def clear(self) -> int:
        """
        Clear all cache entries.

        Returns:
            Number of entries cleared
        """
        count = len(self._cache)
        self._cache.clear()
        logger.info(f"Cache cleared ({count} entries)")
        return count

    def get_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics.

        Returns:
            Dictionary of statistics
        """
        total_requests = self._stats["hits"] + self._stats["misses"]
        hit_rate = (self._stats["hits"] / total_requests * 100) if total_requests > 0 else 0

        return {
            "enabled": self._enabled,
            "size": len(self._cache),
            "max_size": self._max_size,
            "hits": self._stats["hits"],
            "misses": self._stats["misses"],
            "hit_rate": f"{hit_rate:.2f}%",
            "sets": self._stats["sets"],
            "evictions": self._stats["evictions"],
            "expirations": self._stats["expirations"],
            "total_requests": total_requests
        }

    def get_keys(self) -> list[str]:
        """Get all cache keys."""
        return list(self._cache.keys())

    def get_entry_info(self, key: str) -> Optional[Dict[str, Any]]:
        """
        Get information about a cache entry.

        Args:
            key: Cache key

        Returns:
            Dictionary with entry information or None
        """
        if key not in self._cache:
            return None

        entry = self._cache[key]
        return {
            "age": entry.age,
            "ttl": entry.ttl,
            "hits": entry.hits,
            "last_accessed": datetime.fromtimestamp(entry.last_accessed).isoformat(),
            "created_at": datetime.fromtimestamp(entry.created_at).isoformat(),
            "is_expired": entry.is_expired
        }
