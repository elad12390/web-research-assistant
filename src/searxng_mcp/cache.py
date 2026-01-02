"""Simple TTL cache for API responses."""

from __future__ import annotations

import asyncio
import time
from dataclasses import dataclass
from typing import Any

from .config import CACHE_TTL_API_DOCS, CACHE_TTL_CRAWL


@dataclass
class CacheEntry:
    """A cached value with expiration time."""

    value: Any
    expires_at: float


class TTLCache:
    """Simple async-safe TTL cache."""

    def __init__(self, default_ttl: int = 3600) -> None:
        """Initialize cache with default TTL in seconds."""
        self._cache: dict[str, CacheEntry] = {}
        self._lock = asyncio.Lock()
        self.default_ttl = default_ttl

    async def get(self, key: str) -> Any | None:
        """Get a value from cache if it exists and hasn't expired."""
        async with self._lock:
            entry = self._cache.get(key)
            if entry and entry.expires_at > time.time():
                return entry.value
            elif entry:
                del self._cache[key]
            return None

    async def set(self, key: str, value: Any, ttl: int | None = None) -> None:
        """Set a value in cache with optional custom TTL."""
        async with self._lock:
            expires_at = time.time() + (ttl or self.default_ttl)
            self._cache[key] = CacheEntry(value=value, expires_at=expires_at)

    async def delete(self, key: str) -> bool:
        """Delete a key from cache. Returns True if key existed."""
        async with self._lock:
            if key in self._cache:
                del self._cache[key]
                return True
            return False

    async def clear(self) -> int:
        """Clear all entries. Returns count of entries removed."""
        async with self._lock:
            count = len(self._cache)
            self._cache.clear()
            return count

    async def cleanup(self) -> int:
        """Remove expired entries. Returns count removed."""
        async with self._lock:
            now = time.time()
            expired = [k for k, v in self._cache.items() if v.expires_at <= now]
            for k in expired:
                del self._cache[k]
            return len(expired)

    @property
    def size(self) -> int:
        """Current number of entries in cache."""
        return len(self._cache)


# Global cache instances
api_docs_cache = TTLCache(default_ttl=CACHE_TTL_API_DOCS)
crawl_cache = TTLCache(default_ttl=CACHE_TTL_CRAWL)


__all__ = [
    "TTLCache",
    "api_docs_cache",
    "crawl_cache",
]
