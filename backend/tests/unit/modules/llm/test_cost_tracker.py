import pytest
import time

from src.app.llm.cost_tracker import CostTracker


class MockRedis:
    def __init__(self):
        self._store = {}

    async def get(self, key):
        return self._store.get(key)

    async def incrbyfloat(self, key, value):
        current = float(self._store.get(key, 0.0))
        self._store[key] = str(current + value)
        return self._store[key]

    async def expire(self, key, ttl):
        pass

    async def aclose(self):
        pass


class TestCostTracker:
    @pytest.mark.asyncio
    async def test_track_usage_calculates_correct_cost(self):
        mock_redis = MockRedis()
        tracker = CostTracker(mock_redis)

        cost = await tracker.track_usage(
            user_id=1,
            input_tokens=1000000,
            output_tokens=200000,
        )

        assert cost == 2.0

    @pytest.mark.asyncio
    async def test_daily_cost_tracks_per_user(self):
        mock_redis = MockRedis()
        tracker = CostTracker(mock_redis)

        await tracker.track_usage(user_id=1, input_tokens=500000, output_tokens=100000)
        await tracker.track_usage(user_id=2, input_tokens=1000000, output_tokens=0)

        cost_user1 = await tracker.get_daily_cost(user_id=1)
        cost_user2 = await tracker.get_daily_cost(user_id=2)

        assert cost_user1 == 1.0
        assert cost_user2 == 1.0
        assert cost_user1 == cost_user2

    @pytest.mark.asyncio
    async def test_is_under_cap_false_when_exceeded(self):
        mock_redis = MockRedis()
        tracker = CostTracker(mock_redis)

        await tracker.track_usage(user_id=1, input_tokens=10000000, output_tokens=0)

        is_under = await tracker.is_under_cap(user_id=1)

        assert is_under is False
