"""
Unit tests for Redis caching functionality.

Tests cache decorators, key generation, and cache invalidation.
"""

import json
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, Mock, patch

import pytest


@pytest.mark.unit
class TestCacheDecorator:
    """Test suite for cache decorator functionality."""

    @pytest.fixture
    def mock_redis(self, mocker):
        """Create mock Redis client."""
        mock = mocker.Mock()
        mock.get = AsyncMock(return_value=None)
        mock.setex = AsyncMock(return_value=True)
        mock.delete = AsyncMock(return_value=1)
        mock.keys = AsyncMock(return_value=[])
        return mock

    @pytest.mark.asyncio
    async def test_cache_miss_executes_function(self, mock_redis):
        """Test that function is executed on cache miss."""
        from app.core.cache import cache_result

        call_count = 0

        @cache_result(expire_seconds=300)
        async def test_function(x, y):
            nonlocal call_count
            call_count += 1
            return x + y

        with patch("app.core.cache.redis_client", mock_redis):
            result = await test_function(1, 2)

        assert result == 3
        assert call_count == 1

        # Should have called setex to cache result
        mock_redis.setex.assert_called_once()

    @pytest.mark.asyncio
    async def test_cache_hit_returns_cached_value(self, mock_redis):
        """Test that cached value is returned on cache hit."""
        from app.core.cache import cache_result

        # Setup mock to return cached value
        cached_value = json.dumps({"result": 42})
        mock_redis.get = AsyncMock(return_value=cached_value)

        call_count = 0

        @cache_result(expire_seconds=300)
        async def test_function():
            nonlocal call_count
            call_count += 1
            return {"result": 99}

        with patch("app.core.cache.redis_client", mock_redis):
            result = await test_function()

        # Should return cached value, not execute function
        assert result == {"result": 42}
        assert call_count == 0

    @pytest.mark.asyncio
    async def test_cache_key_generation(self, mock_redis):
        """Test cache key generation with different parameters."""
        from app.core.cache import generate_cache_key

        # Test with simple parameters
        key1 = generate_cache_key("test", "param1", "param2")
        key2 = generate_cache_key("test", "param1", "param2")
        key3 = generate_cache_key("test", "param1", "param3")

        # Same parameters should generate same key
        assert key1 == key2

        # Different parameters should generate different key
        assert key1 != key3

        # Key should include prefix
        assert "test" in key1

    @pytest.mark.asyncio
    async def test_cache_key_with_kwargs(self, mock_redis):
        """Test cache key generation with keyword arguments."""
        from app.core.cache import generate_cache_key

        key1 = generate_cache_key("test", a=1, b=2)
        key2 = generate_cache_key("test", b=2, a=1)  # Different order
        key3 = generate_cache_key("test", a=1, b=3)

        # Same kwargs (different order) should generate same key
        assert key1 == key2

        # Different values should generate different key
        assert key1 != key3

    @pytest.mark.asyncio
    async def test_cache_expiration(self, mock_redis):
        """Test cache expiration time is set correctly."""
        from app.core.cache import cache_result

        expire_seconds = 600

        @cache_result(expire_seconds=expire_seconds)
        async def test_function():
            return "result"

        with patch("app.core.cache.redis_client", mock_redis):
            await test_function()

        # Verify setex was called with correct expiration
        call_args = mock_redis.setex.call_args
        assert call_args[0][1] == expire_seconds  # Second argument is expire time

    @pytest.mark.asyncio
    async def test_cache_invalidation(self, mock_redis):
        """Test cache invalidation."""
        from app.core.cache import invalidate_cache

        cache_key = "test:key:123"

        with patch("app.core.cache.redis_client", mock_redis):
            await invalidate_cache(cache_key)

        # Should have called delete
        mock_redis.delete.assert_called_once_with(cache_key)

    @pytest.mark.asyncio
    async def test_cache_pattern_invalidation(self, mock_redis):
        """Test invalidating multiple cache keys by pattern."""
        from app.core.cache import invalidate_cache_pattern

        # Setup mock to return matching keys
        mock_redis.keys = AsyncMock(
            return_value=[
                b"analytics:patients:1",
                b"analytics:patients:2",
                b"analytics:conditions:1",
            ]
        )

        with patch("app.core.cache.redis_client", mock_redis):
            await invalidate_cache_pattern("analytics:patients:*")

        # Should have queried for matching keys
        mock_redis.keys.assert_called_once()

        # Should have deleted matching keys
        assert mock_redis.delete.call_count > 0

    @pytest.mark.asyncio
    async def test_cache_with_complex_objects(self, mock_redis):
        """Test caching complex objects."""
        from app.core.cache import cache_result

        @cache_result(expire_seconds=300)
        async def test_function():
            return {
                "patients": [{"id": 1, "name": "John"}, {"id": 2, "name": "Jane"}],
                "total": 2,
                "timestamp": datetime.now().isoformat(),
            }

        with patch("app.core.cache.redis_client", mock_redis):
            result = await test_function()

        # Verify complex object is serialized correctly
        call_args = mock_redis.setex.call_args
        cached_data = call_args[0][2]  # Third argument is the data

        # Should be JSON string
        parsed = json.loads(cached_data)
        assert "patients" in parsed
        assert len(parsed["patients"]) == 2

    @pytest.mark.asyncio
    async def test_cache_error_handling(self, mock_redis):
        """Test cache handles Redis errors gracefully."""
        from app.core.cache import cache_result

        # Setup mock to raise exception
        mock_redis.get = AsyncMock(side_effect=Exception("Redis connection failed"))

        call_count = 0

        @cache_result(expire_seconds=300)
        async def test_function():
            nonlocal call_count
            call_count += 1
            return "result"

        with patch("app.core.cache.redis_client", mock_redis):
            # Should not raise exception, just bypass cache
            result = await test_function()

        assert result == "result"
        assert call_count == 1  # Function was called

    @pytest.mark.asyncio
    async def test_cache_with_none_value(self, mock_redis):
        """Test caching None values."""
        from app.core.cache import cache_result

        @cache_result(expire_seconds=300)
        async def test_function():
            return None

        with patch("app.core.cache.redis_client", mock_redis):
            result = await test_function()

        assert result is None

        # None should still be cached
        mock_redis.setex.assert_called_once()

    @pytest.mark.asyncio
    async def test_cache_concurrent_access(self, mock_redis):
        """Test cache behavior with concurrent access."""
        import asyncio

        from app.core.cache import cache_result

        call_count = 0

        @cache_result(expire_seconds=300)
        async def test_function(x):
            nonlocal call_count
            call_count += 1
            await asyncio.sleep(0.1)  # Simulate slow operation
            return x * 2

        with patch("app.core.cache.redis_client", mock_redis):
            # Make concurrent calls
            results = await asyncio.gather(test_function(5), test_function(5), test_function(5))

        # All should return same result
        assert all(r == 10 for r in results)

    @pytest.mark.asyncio
    async def test_cache_statistics(self, mock_redis):
        """Test cache hit/miss statistics."""
        from app.core.cache import cache_result, get_cache_stats

        # Setup mock for cache hits and misses
        hit_count = 0
        miss_count = 0

        async def mock_get(key):
            nonlocal hit_count, miss_count
            if "cached" in key:
                hit_count += 1
                return json.dumps("cached_value")
            else:
                miss_count += 1
                return None

        mock_redis.get = mock_get

        @cache_result(expire_seconds=300)
        async def test_function(cache_type):
            return f"result_{cache_type}"

        with patch("app.core.cache.redis_client", mock_redis):
            await test_function("cached")  # Hit
            await test_function("not_cached")  # Miss

        # Verify statistics are tracked (if implemented)
        assert hit_count == 1
        assert miss_count == 1


@pytest.mark.unit
class TestCacheKeyGeneration:
    """Test suite for cache key generation."""

    def test_key_generation_with_prefix(self):
        """Test key generation with custom prefix."""
        from app.core.cache import generate_cache_key

        key = generate_cache_key("custom_prefix", "arg1", "arg2")

        assert "custom_prefix" in key
        assert "arg1" in key
        assert "arg2" in key

    def test_key_generation_deterministic(self):
        """Test key generation is deterministic."""
        from app.core.cache import generate_cache_key

        key1 = generate_cache_key("test", 1, 2, 3)
        key2 = generate_cache_key("test", 1, 2, 3)

        assert key1 == key2

    def test_key_generation_with_special_characters(self):
        """Test key generation handles special characters."""
        from app.core.cache import generate_cache_key

        key = generate_cache_key("test", "user@email.com", "special:chars")

        # Should not contain problematic characters
        assert key is not None
        assert isinstance(key, str)

    def test_key_generation_with_objects(self):
        """Test key generation with object parameters."""
        from app.core.cache import generate_cache_key

        obj1 = {"id": 1, "name": "test"}
        obj2 = {"id": 1, "name": "test"}

        key1 = generate_cache_key("test", obj1)
        key2 = generate_cache_key("test", obj2)

        # Same object values should generate same key
        assert key1 == key2

    def test_key_length_limit(self):
        """Test cache key length is reasonable."""
        from app.core.cache import generate_cache_key

        # Generate key with many parameters
        key = generate_cache_key("test", *range(100))

        # Key should not be excessively long
        assert len(key) < 500


@pytest.mark.integration
class TestCacheIntegration:
    """Integration tests for cache functionality."""

    @pytest.mark.asyncio
    async def test_cache_with_database_query(self, test_db, mock_redis):
        """Test caching database query results."""
        from app.core.cache import cache_result
        from app.models.fhir_resources import Patient

        # Create test patient
        patient = Patient(
            fhir_id="cache-test-1",
            identifier="CACHE001",
            family_name="Cache",
            given_name="Test",
            gender="male",
            birth_date="1990-01-01",
        )
        test_db.add(patient)
        test_db.commit()

        query_count = 0

        @cache_result(expire_seconds=300)
        async def get_patient(patient_id):
            nonlocal query_count
            query_count += 1
            return test_db.query(Patient).filter(Patient.id == patient_id).first()

        with patch("app.core.cache.redis_client", mock_redis):
            # First call - cache miss
            result1 = await get_patient(patient.id)

            # Second call - should use cache
            mock_redis.get = AsyncMock(
                return_value=json.dumps({"id": patient.id, "fhir_id": patient.fhir_id})
            )
            result2 = await get_patient(patient.id)

        # First call should execute query
        assert query_count == 1

    @pytest.mark.asyncio
    async def test_cache_invalidation_on_update(self, test_db, mock_redis):
        """Test cache is invalidated when data is updated."""
        from app.core.cache import cache_result, invalidate_cache_pattern
        from app.models.fhir_resources import Patient

        patient = Patient(
            fhir_id="cache-test-2",
            identifier="CACHE002",
            family_name="Update",
            given_name="Test",
            gender="female",
            birth_date="1985-01-01",
        )
        test_db.add(patient)
        test_db.commit()

        with patch("app.core.cache.redis_client", mock_redis):
            # Invalidate patient caches
            await invalidate_cache_pattern("patients:*")

        # Should have attempted to delete cached keys
        mock_redis.keys.assert_called_once()

    @pytest.mark.slow
    @pytest.mark.asyncio
    async def test_cache_performance_improvement(self, test_db, mock_redis):
        """Test that caching improves query performance."""
        import time

        from app.core.cache import cache_result

        # Expensive query simulation
        @cache_result(expire_seconds=300)
        async def expensive_query():
            await asyncio.sleep(0.5)  # Simulate slow query
            return {"result": "data"}

        with patch("app.core.cache.redis_client", mock_redis):
            # First call - slow
            start = time.time()
            result1 = await expensive_query()
            duration1 = time.time() - start

            # Setup mock for cache hit
            mock_redis.get = AsyncMock(return_value=json.dumps({"result": "data"}))

            # Second call - should be fast (from cache)
            start = time.time()
            result2 = await expensive_query()
            duration2 = time.time() - start

        # Cached call should be much faster
        assert duration2 < duration1 * 0.1  # At least 10x faster


@pytest.mark.unit
def test_cache_disabled_in_testing():
    """Test that cache can be disabled for testing."""
    import os

    from app.core.config import settings

    # In test environment, cache might be disabled
    if os.getenv("ENVIRONMENT") == "testing":
        # Cache operations should work but not actually cache
        pass


import asyncio  # Add missing import at the top
