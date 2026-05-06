import hashlib
import json
from typing import Any

import redis.asyncio as redis

from src.app.core.config import settings


class EnrichmentCache:
    def __init__(self, redis_client: redis.Redis) -> None:
        self._redis = redis_client
        self._ttl_days = settings.redis_enrichment_ttl_days
        self._ttl_seconds = settings.redis_preview_ttl_seconds

    def _normalize_cache_key(self, term: str, language: str, level: str) -> str:
        normalized = f"{term.lower().strip()}:{language}:{level}".encode()
        return f"enrichment:cache:{hashlib.sha256(normalized).hexdigest()}"

    def _preview_cache_key(self, preview_id: str) -> str:
        return f"enrichment:preview:{preview_id}"

    async def get_enrichment(self, term: str, language: str, level: str) -> dict[str, Any] | None:
        key = self._normalize_cache_key(term, language, level)
        cached = await self._redis.get(key)
        if cached:
            return json.loads(cached)
        return None

    async def set_enrichment(
        self, term: str, language: str, level: str, data: dict[str, Any]
    ) -> None:
        key = self._normalize_cache_key(term, language, level)
        await self._redis.setex(key, self._ttl_days * 86400, json.dumps(data))

    async def get_preview(self, preview_id: str) -> dict[str, Any] | None:
        key = self._preview_cache_key(preview_id)
        cached = await self._redis.get(key)
        if cached:
            return json.loads(cached)
        return None

    async def set_preview(self, preview_id: str, data: dict[str, Any]) -> None:
        key = self._preview_cache_key(preview_id)
        await self._redis.setex(key, self._ttl_seconds, json.dumps(data))
