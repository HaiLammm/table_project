from typing import Any

import redis.asyncio as redis

from src.app.db.session import async_session_factory
from src.app.llm import LLMGateway
from src.app.modules.dictionary.application.services import JMdictService
from src.app.modules.vocabulary.infrastructure.repository import VocabularyRepositoryImpl


async def process_enrichment_job(ctx: dict[str, object]) -> dict[str, Any]:
    data = ctx.get("data", {})

    term: str = data.get("term", "")
    language: str = data.get("language", "en")
    level: str = data.get("level", "A2")
    user_id: int | None = data.get("user_id")
    term_id: int | None = data.get("term_id")

    if not term:
        raise ValueError("term is required for enrichment job")

    redis_url: str = data.get("redis_url", "redis://localhost:6380/0")
    redis_client = redis.from_url(redis_url)
    try:
        jmdict = JMdictService()
        gateway = LLMGateway(redis_client, jmdict)

        result = await gateway.enrich_term(term, language, level, user_id)

        await _persist_enrichment_result(
            term_id=term_id,
            result=result,
            language=language,
        )

        return {
            "status": "success",
            "term": term,
            "validated_against_jmdict": result.validated_against_jmdict,
        }
    finally:
        await redis_client.aclose()


async def _persist_enrichment_result(
    term_id: int | None,
    result: Any,
    language: str,
) -> None:
    async with async_session_factory() as session:
        repo = VocabularyRepositoryImpl(session)

        if term_id is None:
            existing = await repo.find_by_value(result.term, language)
            if existing:
                term_id = existing.id

        if term_id is None:
            from src.app.modules.vocabulary.domain.entities import VocabularyTerm

            new_term = VocabularyTerm(
                term=result.term,
                language=language,
                cefr_level=result.cefr_level,
                jlpt_level=result.jlpt_level,
                part_of_speech=None,
            )
            created = await repo.create_term(new_term)
            term_id = created.id

        if term_id is not None and result.definition:
            from src.app.modules.vocabulary.domain.entities import VocabularyDefinition

            definition = VocabularyDefinition(
                term_id=term_id,
                language=language,
                definition=result.definition,
                ipa=result.ipa,
                examples=list(result.examples),
                source="llm",
                validated_against_jmdict=result.validated_against_jmdict,
            )
            await repo.create_definition(definition)


def enrich_term_job_id(term: str, language: str, level: str) -> str:
    return f"enrichment:{term}:{language}:{level}"


async def enqueue_enrichment_job(
    redis_pool: redis.Redis,
    term: str,
    language: str,
    level: str,
    user_id: int | None = None,
    term_id: int | None = None,
) -> str:
    job_id = enrich_term_job_id(term, language, level)
    await redis_pool.enqueue_job(
        "process_enrichment_job",
        job_id=job_id,
        data={
            "term": term,
            "language": language,
            "level": level,
            "user_id": user_id,
            "term_id": term_id,
            "redis_url": str(
                redis_pool.connection_pool.connection_kwargs.get("url", "redis://localhost:6380/0")
            ),
        },
        _job_id=job_id,
    )
    return job_id


class EnrichmentWorker:
    def __init__(self, redis_client: redis.Redis) -> None:
        self._redis = redis_client
        self._jmdict = JMdictService()
        self._gateway = LLMGateway(redis_client, self._jmdict)

    async def process(self, job_data: dict[str, Any]) -> dict[str, Any]:
        term = job_data.get("term", "")
        language = job_data.get("language", "en")
        level = job_data.get("level", "A2")
        user_id = job_data.get("user_id")
        term_id = job_data.get("term_id")

        result = await self._gateway.enrich_term(term, language, level, user_id)

        await _persist_enrichment_result(term_id, result, language)

        return {
            "status": "success",
            "term": term,
            "validated_against_jmdict": result.validated_against_jmdict,
        }
