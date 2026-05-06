import pytest

from src.app.llm.cache import EnrichmentCache


@pytest.fixture
def mock_redis():
    class MockRedis:
        def __init__(self):
            self._store = {}

        async def get(self, key):
            return self._store.get(key)

        async def setex(self, key, ttl, value):
            self._store[key] = value

        async def aclose(self):
            pass

    return MockRedis()


class TestEnrichmentCache:
    def test_normalize_cache_key_produces_consistent_keys(self, mock_redis):
        cache = EnrichmentCache(mock_redis)

        key1 = cache._normalize_cache_key("protocol", "en", "B2")
        key2 = cache._normalize_cache_key("protocol", "en", "B2")
        key3 = cache._normalize_cache_key("Protocol", "en", "B2")

        assert key1 == key2
        assert key1 == key3

    def test_normalize_cache_key_different_for_different_levels(self, mock_redis):
        cache = EnrichmentCache(mock_redis)

        key1 = cache._normalize_cache_key("protocol", "en", "B2")
        key2 = cache._normalize_cache_key("protocol", "en", "C1")

        assert key1 != key2

    def test_preview_cache_key_format(self, mock_redis):
        cache = EnrichmentCache(mock_redis)

        key = cache._preview_cache_key("preview-123")

        assert key == "enrichment:preview:preview-123"
