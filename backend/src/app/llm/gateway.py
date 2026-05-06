import uuid
from typing import Any

import redis.asyncio as redis

from src.app.llm.cache import EnrichmentCache
from src.app.llm.cost_tracker import CostTracker
from src.app.llm.providers import LLMProvider
from src.app.llm.providers.anthropic import AnthropicProvider
from src.app.llm.providers.deepseek import DeepSeekProvider
from src.app.llm.providers.google import GoogleProvider
from src.app.llm.schemas import EnrichmentResult
from src.app.modules.dictionary.application.services import JMdictService


class LLMGateway:
    def __init__(
        self,
        redis_client: redis.Redis,
        jmdict_service: JMdictService | None = None,
    ) -> None:
        self._cache = EnrichmentCache(redis_client)
        self._cost_tracker = CostTracker(redis_client)
        self._jmdict = jmdict_service or JMdictService()
        self._providers: list[tuple[LLMProvider, str]] = [
            (AnthropicProvider(), "anthropic"),
            (GoogleProvider(), "google"),
            (DeepSeekProvider(), "deepseek"),
        ]

    def _build_enrichment_prompt(self, term: str, language: str, level: str) -> str:
        level_hint = f"CEFR {level}" if language == "en" else f"JLPT N{level}"
        return (
            f"Provide vocabulary enrichment for the term '{term}' ({language}, {level_hint}). "
            "Return valid JSON with these fields: term, language, definition (1-2 sentences), "
            "ipa (phonetic pronunciation), cefr_level (for English) or jlpt_level (for Japanese), "
            "examples (array of 2-3 example sentences), and related_terms (array of 5 words). "
            "For Japanese terms, include kanji and kana forms. "
            "Return only valid JSON matching this schema: "
            '{"term": "", "language": "", "definition": "", "ipa": null, "cefr_level": null, '
            '"jlpt_level": null, "examples": [], "related_terms": []}'
        )

    async def enrich_term(
        self, term: str, language: str, level: str, user_id: int | None = None
    ) -> EnrichmentResult:
        cached = await self._cache.get_enrichment(term, language, level)
        if cached:
            return EnrichmentResult.model_validate(cached)

        provider_result = await self._call_with_fallback(level, term, language, level, user_id)

        result = self._build_enrichment_result(provider_result, term, language, level)

        await self._cache.set_enrichment(term, language, level, result.model_dump(mode="json"))

        return result

    async def _call_with_fallback(
        self, retry_count: int, term: str, language: str, level: str, user_id: int | None
    ) -> dict[str, Any]:
        last_error: Exception | None = None

        for provider, _provider_name in self._providers:
            try:
                if not await self._cost_tracker.is_under_cap(user_id):
                    raise RuntimeError(f"Daily cost cap exceeded for user {user_id}")

                prompt = self._build_enrichment_prompt(term, language, level)
                response = await provider.complete(prompt)
                await self._cost_tracker.track_usage(
                    user_id,
                    response.input_tokens,
                    response.output_tokens,
                )

                if hasattr(provider, "parse_enrichment_response"):
                    parsed = provider.parse_enrichment_response(response)
                else:
                    parsed = response.raw_response.get("text", "{}")

                if isinstance(parsed, dict) and "error" not in parsed:
                    return parsed

            except Exception as e:
                last_error = e
                continue

        if last_error:
            raise last_error
        raise RuntimeError("All LLM providers failed")

    def _build_enrichment_result(
        self, provider_data: dict[str, Any], term: str, language: str, level: str
    ) -> EnrichmentResult:
        validated_jmdict = False
        if language == "jp":
            definition = provider_data.get("definition", "")
            if definition:
                validated_jmdict = self._jmdict.is_definition_valid(term, definition)

        return EnrichmentResult(
            term=provider_data.get("term", term),
            language=language,
            definition=provider_data.get("definition", ""),
            ipa=provider_data.get("ipa"),
            cefr_level=provider_data.get("cefr_level"),
            jlpt_level=provider_data.get("jlpt_level"),
            examples=list(provider_data.get("examples", [])),
            related_terms=list(provider_data.get("related_terms", [])),
            source="llm",
            validated_against_jmdict=validated_jmdict,
        )


class GatewayOrchestrator:
    def __init__(
        self,
        redis_client: redis.Redis,
        jmdict_service: JMdictService | None = None,
    ) -> None:
        self._gateway = LLMGateway(redis_client, jmdict_service)
        self._cache = EnrichmentCache(redis_client)

    async def generate_preview_candidates(
        self,
        topic: str,
        language: str,
        level: str,
        count: int,
        existing_term_ids: list[int],
    ) -> tuple[str, list[EnrichmentResult]]:
        gap_count = max(0, count - len(existing_term_ids))
        if gap_count == 0:
            return "", []

        candidates: list[EnrichmentResult] = []
        for _ in range(gap_count):
            result = await self._gateway.enrich_term(topic, language, level)
            candidates.append(result)

        preview_id = str(uuid.uuid4())
        preview_candidates = []
        for c in candidates:
            candidate_data = c.model_dump(mode="json")
            candidate_data["candidate_id"] = f"llm_{uuid.uuid4().hex[:8]}"
            preview_candidates.append(candidate_data)

        preview_data = {
            "topic": topic,
            "language": language,
            "level": level,
            "candidates": preview_candidates,
        }
        await self._cache.set_preview(preview_id, preview_data)

        return preview_id, candidates
