"""
Redis cache service.
Provides get/set/delete with JSON serialization and TTL support.
"""
from __future__ import annotations

import json
from typing import Any, Optional

import redis.asyncio as aioredis

from core.config import settings
from core.logging_config import get_logger

logger = get_logger(__name__)

_redis: aioredis.Redis | None = None


async def get_redis() -> aioredis.Redis:
    global _redis
    if _redis is None:
        _redis = aioredis.from_url(
            settings.REDIS_URL,
            encoding="utf-8",
            decode_responses=True,
            socket_connect_timeout=5,
            socket_timeout=5,
            retry_on_timeout=True,
            health_check_interval=30,
        )
    return _redis


async def close_redis() -> None:
    global _redis
    if _redis:
        await _redis.aclose()
        _redis = None
    logger.info("redis_closed")


class CacheService:
    """High-level cache operations."""

    def __init__(self, prefix: str = "bnx"):
        self.prefix = prefix

    def _key(self, key: str) -> str:
        return f"{self.prefix}:{key}"

    async def get(self, key: str) -> Optional[Any]:
        try:
            r = await get_redis()
            value = await r.get(self._key(key))
            if value is None:
                return None
            return json.loads(value)
        except Exception as e:
            logger.warning("cache_get_error", key=key, error=str(e))
            return None

    async def set(
        self, key: str, value: Any, ttl: int = settings.CACHE_TTL
    ) -> bool:
        try:
            r = await get_redis()
            serialized = json.dumps(value, ensure_ascii=False, default=str)
            await r.set(self._key(key), serialized, ex=ttl)
            return True
        except Exception as e:
            logger.warning("cache_set_error", key=key, error=str(e))
            return False

    async def delete(self, key: str) -> bool:
        try:
            r = await get_redis()
            await r.delete(self._key(key))
            return True
        except Exception as e:
            logger.warning("cache_delete_error", key=key, error=str(e))
            return False

    async def exists(self, key: str) -> bool:
        try:
            r = await get_redis()
            return bool(await r.exists(self._key(key)))
        except Exception:
            return False

    async def increment(self, key: str, amount: int = 1, ttl: Optional[int] = None) -> int:
        try:
            r = await get_redis()
            full_key = self._key(key)
            val = await r.incrby(full_key, amount)
            if ttl and val == amount:
                await r.expire(full_key, ttl)
            return val
        except Exception as e:
            logger.warning("cache_increment_error", key=key, error=str(e))
            return 0

    async def get_ttl(self, key: str) -> int:
        try:
            r = await get_redis()
            return await r.ttl(self._key(key))
        except Exception:
            return -1

    async def flush_pattern(self, pattern: str) -> int:
        """Delete all keys matching pattern. Use carefully."""
        try:
            r = await get_redis()
            keys = await r.keys(self._key(pattern))
            if keys:
                await r.delete(*keys)
            return len(keys)
        except Exception as e:
            logger.warning("cache_flush_error", pattern=pattern, error=str(e))
            return 0


# Singleton instances
search_cache = CacheService(prefix="search")
user_cache = CacheService(prefix="user")
rate_limit_cache = CacheService(prefix="ratelimit")
price_cache = CacheService(prefix="price")
