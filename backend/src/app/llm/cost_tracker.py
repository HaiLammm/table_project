import time

import redis.asyncio as redis

from src.app.core.config import settings


class CostTracker:
    def __init__(self, redis_client: redis.Redis) -> None:
        self._redis = redis_client
        self._daily_cap = settings.daily_cost_cap_usd
        self._window_seconds = 86400

    def _cost_key(self, user_id: int | None) -> str:
        bucket = user_id if user_id is not None else "anonymous"
        today = int(time.time() // 86400)
        return f"llm:cost:{bucket}:{today}"

    async def track_usage(
        self, user_id: int | None, input_tokens: int, output_tokens: int
    ) -> float:
        input_cost = input_tokens * 0.000001
        output_cost = output_tokens * 0.000005
        total_cost = input_cost + output_cost

        key = self._cost_key(user_id)
        await self._redis.incrbyfloat(key, total_cost)
        await self._redis.expire(key, self._window_seconds)

        return total_cost

    async def get_daily_cost(self, user_id: int | None) -> float:
        key = self._cost_key(user_id)
        cost = await self._redis.get(key)
        return float(cost) if cost else 0.0

    async def is_under_cap(self, user_id: int | None) -> bool:
        current_cost = await self.get_daily_cost(user_id)
        return current_cost < self._daily_cap
