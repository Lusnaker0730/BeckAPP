"""
Redis Cache Module for FHIR Analytics Platform

Provides caching functionality to improve API performance by storing
frequently accessed data in Redis memory store.
"""

import json
import redis
import hashlib
from functools import wraps
from typing import Optional, Any, Callable
import logging

from .config import settings

logger = logging.getLogger(__name__)

# Initialize Redis client
try:
    redis_client = redis.from_url(
        settings.REDIS_URL,
        decode_responses=True,
        socket_connect_timeout=5,
        socket_timeout=5,
        retry_on_timeout=True
    )
    # Test connection
    redis_client.ping()
    logger.info("✅ Redis connection established successfully")
    REDIS_AVAILABLE = True
except (redis.RedisError, ConnectionError) as e:
    logger.warning(f"⚠️  Redis not available: {e}. Caching will be disabled.")
    redis_client = None
    REDIS_AVAILABLE = False


def generate_cache_key(prefix: str, *args, **kwargs) -> str:
    """
    Generate a unique cache key based on function arguments
    
    Args:
        prefix: Key prefix (usually function name)
        *args: Positional arguments
        **kwargs: Keyword arguments
    
    Returns:
        A unique cache key string
    """
    # Create a string representation of arguments
    key_parts = [prefix]
    
    # Add positional arguments
    for arg in args:
        if hasattr(arg, '__dict__'):
            # Skip complex objects like database sessions
            continue
        key_parts.append(str(arg))
    
    # Add keyword arguments (sorted for consistency)
    for k, v in sorted(kwargs.items()):
        if k in ['db', 'current_user', 'session']:
            # Skip database and session objects
            continue
        key_parts.append(f"{k}={v}")
    
    # Create key string
    key_string = ":".join(key_parts)
    
    # Hash if too long (Redis key limit is 512MB, but keep it short)
    if len(key_string) > 200:
        key_hash = hashlib.md5(key_string.encode()).hexdigest()
        return f"{prefix}:{key_hash}"
    
    return key_string


def cache_result(
    expire_seconds: int = 300,
    key_prefix: Optional[str] = None
) -> Callable:
    """
    Decorator to cache function results in Redis
    
    Usage:
        @cache_result(expire_seconds=600, key_prefix="diagnosis")
        async def get_diagnosis_data(diagnosis: str, db: Session):
            # expensive database query
            return result
    
    Args:
        expire_seconds: Cache expiration time in seconds (default: 5 minutes)
        key_prefix: Custom prefix for cache key (default: function name)
    
    Returns:
        Decorated function with caching capability
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            # Skip caching if Redis is not available
            if not REDIS_AVAILABLE:
                return await func(*args, **kwargs)
            
            # Generate cache key
            prefix = key_prefix or func.__name__
            cache_key = generate_cache_key(prefix, *args, **kwargs)
            
            try:
                # Try to get cached result
                cached_value = redis_client.get(cache_key)
                
                if cached_value:
                    logger.info(f"✅ Cache HIT: {cache_key[:80]}")
                    try:
                        return json.loads(cached_value)
                    except json.JSONDecodeError:
                        logger.warning(f"Failed to decode cached value for {cache_key}")
                        # Continue to execute function
                
                logger.info(f"❌ Cache MISS: {cache_key[:80]}")
                
                # Execute the original function
                result = await func(*args, **kwargs)
                
                # Cache the result
                try:
                    serialized = json.dumps(result, default=str)
                    redis_client.setex(cache_key, expire_seconds, serialized)
                    logger.debug(f"💾 Cached result for {cache_key[:80]} (expires in {expire_seconds}s)")
                except (TypeError, redis.RedisError) as e:
                    logger.warning(f"Failed to cache result: {e}")
                
                return result
                
            except redis.RedisError as e:
                # Graceful degradation: if Redis fails, just execute the function
                logger.error(f"⚠️  Redis error: {e}, executing without cache")
                return await func(*args, **kwargs)
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            """Synchronous version of the wrapper"""
            if not REDIS_AVAILABLE:
                return func(*args, **kwargs)
            
            prefix = key_prefix or func.__name__
            cache_key = generate_cache_key(prefix, *args, **kwargs)
            
            try:
                cached_value = redis_client.get(cache_key)
                
                if cached_value:
                    logger.info(f"✅ Cache HIT: {cache_key[:80]}")
                    return json.loads(cached_value)
                
                logger.info(f"❌ Cache MISS: {cache_key[:80]}")
                result = func(*args, **kwargs)
                
                try:
                    serialized = json.dumps(result, default=str)
                    redis_client.setex(cache_key, expire_seconds, serialized)
                except (TypeError, redis.RedisError) as e:
                    logger.warning(f"Failed to cache result: {e}")
                
                return result
                
            except redis.RedisError as e:
                logger.error(f"⚠️  Redis error: {e}, executing without cache")
                return func(*args, **kwargs)
        
        # Return appropriate wrapper based on function type
        import asyncio
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator


def invalidate_cache(pattern: str) -> int:
    """
    Delete all cache entries matching the given pattern
    
    Args:
        pattern: Redis key pattern (e.g., "diagnosis:*" or "top_conditions:*")
    
    Returns:
        Number of keys deleted
    """
    if not REDIS_AVAILABLE:
        logger.warning("Redis not available, cannot invalidate cache")
        return 0
    
    try:
        keys = redis_client.keys(pattern)
        if keys:
            deleted = redis_client.delete(*keys)
            logger.info(f"🗑️  Invalidated {deleted} cache entries matching '{pattern}'")
            return deleted
        return 0
    except redis.RedisError as e:
        logger.error(f"⚠️  Error invalidating cache: {e}")
        return 0


def clear_all_cache() -> bool:
    """
    Clear all cache entries (use with caution!)
    
    Returns:
        True if successful, False otherwise
    """
    if not REDIS_AVAILABLE:
        return False
    
    try:
        redis_client.flushdb()
        logger.warning("🗑️  Cleared ALL cache entries")
        return True
    except redis.RedisError as e:
        logger.error(f"⚠️  Error clearing cache: {e}")
        return False


def get_cache_stats() -> Optional[dict]:
    """
    Get Redis cache statistics
    
    Returns:
        Dictionary with cache statistics or None if Redis is unavailable
    """
    if not REDIS_AVAILABLE:
        return None
    
    try:
        info = redis_client.info("stats")
        memory_info = redis_client.info("memory")
        
        total_commands = info.get("total_commands_processed", 0)
        hits = info.get("keyspace_hits", 0)
        misses = info.get("keyspace_misses", 0)
        total_lookups = hits + misses
        
        return {
            "status": "connected",
            "total_keys": redis_client.dbsize(),
            "memory_used_mb": round(memory_info.get("used_memory", 0) / 1024 / 1024, 2),
            "memory_peak_mb": round(memory_info.get("used_memory_peak", 0) / 1024 / 1024, 2),
            "hits": hits,
            "misses": misses,
            "hit_rate": round(hits / max(total_lookups, 1) * 100, 2),
            "total_commands": total_commands,
            "connected_clients": redis_client.client_list().__len__() if hasattr(redis_client, 'client_list') else 0,
        }
    except redis.RedisError as e:
        logger.error(f"⚠️  Error getting cache stats: {e}")
        return {"status": "error", "error": str(e)}


def set_cache(key: str, value: Any, expire_seconds: int = 300) -> bool:
    """
    Manually set a cache entry
    
    Args:
        key: Cache key
        value: Value to cache (will be JSON serialized)
        expire_seconds: Expiration time in seconds
    
    Returns:
        True if successful, False otherwise
    """
    if not REDIS_AVAILABLE:
        return False
    
    try:
        serialized = json.dumps(value, default=str)
        redis_client.setex(key, expire_seconds, serialized)
        return True
    except (TypeError, redis.RedisError) as e:
        logger.error(f"⚠️  Error setting cache: {e}")
        return False


def get_cache(key: str) -> Optional[Any]:
    """
    Manually get a cache entry
    
    Args:
        key: Cache key
    
    Returns:
        Cached value or None if not found
    """
    if not REDIS_AVAILABLE:
        return None
    
    try:
        cached_value = redis_client.get(key)
        if cached_value:
            return json.loads(cached_value)
        return None
    except (json.JSONDecodeError, redis.RedisError) as e:
        logger.error(f"⚠️  Error getting cache: {e}")
        return None


# Cache invalidation helpers for specific scenarios
def invalidate_diagnosis_cache():
    """Invalidate all diagnosis-related cache"""
    invalidate_cache("diagnosis:*")
    invalidate_cache("get_diagnosis_analysis:*")


def invalidate_analytics_cache():
    """Invalidate all analytics cache"""
    invalidate_cache("top_conditions:*")
    invalidate_cache("patient_demographics:*")
    invalidate_cache("available_diagnoses:*")


def invalidate_all_after_etl():
    """Invalidate all relevant cache after ETL job completes"""
    patterns = [
        "diagnosis:*",
        "top_conditions:*",
        "patient_demographics:*",
        "available_diagnoses:*",
        "get_*:*"
    ]
    total_deleted = 0
    for pattern in patterns:
        total_deleted += invalidate_cache(pattern)
    logger.info(f"🔄 Invalidated {total_deleted} cache entries after ETL completion")
    return total_deleted

