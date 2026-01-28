"""
Redis caching utilities
"""
import json
import redis
from typing import Optional, Any
from app.config import settings

# Redis client configuration
redis_client = None

try:
    redis_client = redis.Redis(
        host='redis',
        port=6379,
        db=0,
        decode_responses=True,
        socket_connect_timeout=2,
        socket_timeout=2
    )
    # Test connection
    redis_client.ping()
except (redis.ConnectionError, redis.TimeoutError):
    # Redis not available, caching will be disabled
    redis_client = None


def cache_get(key: str) -> Optional[Any]:
    """
    Get value from cache.
    Returns None if key doesn't exist or Redis is unavailable.
    """
    if not redis_client:
        return None

    try:
        data = redis_client.get(key)
        if data:
            return json.loads(data)
        return None
    except (redis.RedisError, json.JSONDecodeError):
        return None


def cache_set(key: str, value: Any, expire: int = 300) -> bool:
    """
    Set value in cache with expiration time in seconds.
    Returns True if successful, False otherwise.
    """
    if not redis_client:
        return False

    try:
        serialized = json.dumps(value)
        redis_client.setex(key, expire, serialized)
        return True
    except (redis.RedisError, TypeError, json.JSONEncodeError):
        return False


def cache_delete(key: str) -> bool:
    """
    Delete key from cache.
    Returns True if key was deleted, False otherwise.
    """
    if not redis_client:
        return False

    try:
        redis_client.delete(key)
        return True
    except redis.RedisError:
        return False


def cache_clear_pattern(pattern: str) -> int:
    """
    Delete all keys matching pattern.
    Returns number of keys deleted.
    """
    if not redis_client:
        return 0

    try:
        keys = redis_client.keys(pattern)
        if keys:
            return redis_client.delete(*keys)
        return 0
    except redis.RedisError:
        return 0


def is_cache_available() -> bool:
    """
    Check if Redis cache is available.
    """
    if not redis_client:
        return False

    try:
        redis_client.ping()
        return True
    except redis.RedisError:
        return False
