from typing import Any

import redis.asyncio as redis
import structlog
from sqlalchemy import select

from src.app.db.session import async_session_factory
from src.app.modules.vocabulary.infrastructure.models import VocabularyTermModel
from src.app.modules.vocabulary.infrastructure.repository import VocabularyRepositoryImpl

logger = structlog.get_logger().bind(module="corpus_sync")


async def process_corpus_sync_job(ctx: dict[str, object]) -> dict[str, Any]:
    job_id = ctx.get("job_id", "")
    data = ctx.get("data", {})

    language: str = data.get("language", "en")
    min_level: str = data.get("min_level", "A1")
    max_results: int = data.get("max_results", 100)

    logger.info("corpus_sync_job_started", job_id=job_id, language=language)

    sync_stats = await _run_corpus_sync(language, min_level, max_results)

    logger.info(
        "corpus_sync_job_completed",
        job_id=job_id,
        terms_merged=sync_stats["terms_merged"],
        duplicates_skipped=sync_stats["duplicates_skipped"],
    )

    return {
        "status": "success",
        "language": language,
        "terms_merged": sync_stats["terms_merged"],
        "duplicates_skipped": sync_stats["duplicates_skipped"],
    }


async def _run_corpus_sync(
    language: str,
    min_level: str,
    max_results: int,
) -> dict[str, int]:
    terms_merged = 0
    duplicates_skipped = 0

    async with async_session_factory() as session:
        repo = VocabularyRepositoryImpl(session)

        result = await session.execute(
            select(VocabularyTermModel)
            .where(
                VocabularyTermModel.language == language,
                VocabularyTermModel.source == "llm",
            )
            .limit(max_results)
        )
        llm_terms = result.scalars().all()

        for term_model in llm_terms:
            existing = await repo.get_term_by_value(term_model.term, term_model.language)
            if existing is not None:
                duplicates_skipped += 1
            else:
                from src.app.modules.vocabulary.domain.entities import VocabularyTerm

                new_term = VocabularyTerm(
                    term=term_model.term,
                    language=term_model.language,
                    cefr_level=term_model.cefr_level,
                    jlpt_level=term_model.jlpt_level,
                    part_of_speech=term_model.part_of_speech,
                )
                await repo.create_term(new_term)
                terms_merged += 1

    return {
        "terms_merged": terms_merged,
        "duplicates_skipped": duplicates_skipped,
    }


def corpus_sync_job_id(language: str) -> str:
    return f"corpus_sync:{language}"


async def enqueue_corpus_sync_job(
    redis_pool: redis.Redis,
    language: str = "en",
    min_level: str = "A1",
) -> str:
    job_id = corpus_sync_job_id(language)
    await redis_pool.enqueue_job(
        "process_corpus_sync_job",
        job_id=job_id,
        data={
            "language": language,
            "min_level": min_level,
            "max_results": 100,
        },
        _job_id=job_id,
    )
    return job_id
