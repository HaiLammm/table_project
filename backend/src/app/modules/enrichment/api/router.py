from collections.abc import AsyncGenerator
from typing import Annotated

import redis.asyncio as redis
from fastapi import APIRouter, Depends

from src.app.core.config import settings
from src.app.llm.cache import EnrichmentCache
from src.app.modules.enrichment.api.dependencies import SessionDependency
from src.app.modules.enrichment.api.schemas import (
    EnrichedTermResponse,
    VocabularyRequestConfirm,
    VocabularyRequestConfirmResponse,
    VocabularyRequestCreate,
    VocabularyRequestPreviewResponse,
)
from src.app.modules.vocabulary.domain.entities import VocabularyDefinition, VocabularyTerm
from src.app.modules.vocabulary.infrastructure.repository import VocabularyRepositoryImpl

enrichment_router = APIRouter(prefix="/vocabulary_requests", tags=["vocabulary-requests"])


async def get_redis_pool() -> AsyncGenerator[redis.Redis, None]:
    pool = redis.from_url(settings.redis_url)
    try:
        yield pool
    finally:
        await pool.aclose()


RedisPoolDependency = Annotated[redis.Redis, Depends(get_redis_pool)]


@enrichment_router.post("/preview", response_model=VocabularyRequestPreviewResponse)
async def preview_vocabulary_request(
    payload: VocabularyRequestCreate,
    session: SessionDependency,
    redis_pool: RedisPoolDependency,
) -> VocabularyRequestPreviewResponse:
    from src.app.modules.enrichment.application.services import GatewayEnrichmentService

    service = GatewayEnrichmentService(session, redis_pool)
    terms = await service.find_terms_for_request(
        topic=payload.topic,
        language=payload.language,
        level=payload.level,
        count=payload.count,
    )
    corpus_match_count = len([t for t in terms if t.source == "corpus"])
    preview_id = terms[0].preview_id if terms else None

    return VocabularyRequestPreviewResponse(
        preview_id=preview_id,
        terms=[EnrichedTermResponse.model_validate(t) for t in terms],
        corpus_match_count=corpus_match_count,
        gap_count=max(0, payload.count - len(terms)),
        requested_count=payload.count,
    )


@enrichment_router.post("/confirm", response_model=VocabularyRequestConfirmResponse)
async def confirm_vocabulary_request(
    payload: VocabularyRequestConfirm,
    session: SessionDependency,
    redis_pool: RedisPoolDependency,
) -> VocabularyRequestConfirmResponse:
    cache = EnrichmentCache(redis_pool)
    preview_data = await cache.get_preview(payload.preview_id)

    repo = VocabularyRepositoryImpl(session)

    added = 0
    skipped = 0

    for candidate_id in payload.selected_candidate_ids:
        if preview_data:
            candidates = preview_data.get("candidates", [])
            matching = [c for c in candidates if c.get("candidate_id") == candidate_id]
            if matching:
                candidate = matching[0]
                new_term = VocabularyTerm(
                    term=candidate.get("term", ""),
                    language=candidate.get("language", "en"),
                    cefr_level=candidate.get("cefr_level"),
                    jlpt_level=candidate.get("jlpt_level"),
                )
                created = await repo.create_term(new_term)
                term_id = created.id

                if term_id is not None and candidate.get("definition"):
                    definition = VocabularyDefinition(
                        term_id=term_id,
                        language=candidate.get("language", "en"),
                        definition=candidate.get("definition", ""),
                        ipa=candidate.get("ipa"),
                        examples=list(candidate.get("examples", [])),
                        source="llm",
                        validated_against_jmdict=candidate.get("validated_against_jmdict", False),
                    )
                    await repo.create_definition(definition)
                added += 1
                continue

        skipped += 1

    return VocabularyRequestConfirmResponse(added_count=added, skipped_count=skipped)
