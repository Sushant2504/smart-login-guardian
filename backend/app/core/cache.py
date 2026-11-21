"""
Redis cache utilities for distributed caching
"""
from typing import Optional, Any
import json
import redis
from functools import wraps
from app.config import settings
from app.core import get_logger

logger = get_logger(__name__)

# Global Redis connection pool
_redis_client: Optional[redis.Redis] = None


def get_redis() -> redis.Redis:
    """
    Get Redis client instance (singleton pattern)
    """
    global _redis_client

    if _redis_client is None:
        try:
            _redis_client = redis.from_url(
                settings.REDIS_URL,
                decode_responses=True,
                encoding="utf-8",
                max_connections=50
            )
            # Test connection
            _redis_client.ping()
            logger.info("Redis connection established")
        except Exception as e:
            logger.error("Failed to connect to Redis", error=str(e))
            # Create a dummy client that always fails gracefully
            _redis_client = None

    return _redis_client


def close_redis():
    """
    Close Redis connection
    """
    global _redis_client
    if _redis_client:
        _redis_client.close()
        _redis_client = None
        logger.info("Redis connection closed")


class Cache:
    """
    Cache utility class for common caching operations
    """

    def __init__(self, redis_client: Optional[redis.Redis] = None):
        self.redis = redis_client or get_redis()

    def get(self, key: str) -> Optional[Any]:
        """
        Get value from cache
        """
        if not self.redis:
            return None

        try:
            value = self.redis.get(key)
            if value:
                return json.loads(value)
            return None
        except Exception as e:
            logger.error("Cache get error", key=key, error=str(e))
            return None

    def set(self, key: str, value: Any, ttl: int = None) -> bool:
        """
        Set value in cache with optional TTL (seconds)
        """
        if not self.redis:
            return False

        try:
            serialized = json.dumps(value)
            if ttl:
                self.redis.setex(key, ttl, serialized)
            else:
                self.redis.set(key, serialized)
            return True
        except Exception as e:
            logger.error("Cache set error", key=key, error=str(e))
            return False

    def delete(self, key: str) -> bool:
        """
        Delete key from cache
        """
        if not self.redis:
            return False

        try:
            self.redis.delete(key)
            return True
        except Exception as e:
            logger.error("Cache delete error", key=key, error=str(e))
            return False

    def exists(self, key: str) -> bool:
        """
        Check if key exists in cache
        """
        if not self.redis:
            return False

        try:
            return self.redis.exists(key) > 0
        except Exception as e:
            logger.error("Cache exists error", key=key, error=str(e))
            return False

    def clear_pattern(self, pattern: str) -> int:
        """
        Clear all keys matching pattern
        """
        if not self.redis:
            return 0

        try:
            keys = self.redis.keys(pattern)
            if keys:
                return self.redis.delete(*keys)
            return 0
        except Exception as e:
            logger.error("Cache clear error", pattern=pattern, error=str(e))
            return 0


def cached(ttl: int = 3600, prefix: str = "cache"):
    """
    Decorator to cache function results

    Args:
        ttl: Time to live in seconds (default: 1 hour)
        prefix: Cache key prefix
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Generate cache key from function name and arguments
            cache_key = f"{prefix}:{func.__name__}:{hash((args, tuple(sorted(kwargs.items()))))}"

            # Try to get from cache
            cache = Cache()
            cached_result = cache.get(cache_key)

            if cached_result is not None:
                logger.debug("Cache hit", key=cache_key)
                return cached_result

            # Execute function
            result = await func(*args, **kwargs)

            # Store in cache
            cache.set(cache_key, result, ttl)
            logger.debug("Cache miss - stored", key=cache_key)

            return result

        return wrapper
    return decorator
