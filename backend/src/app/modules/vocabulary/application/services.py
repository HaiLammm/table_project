from typing import TypedDict

import structlog

from src.app.modules.vocabulary.application.csv_parser import ParseResult
from src.app.modules.vocabulary.domain.entities import VocabularyDefinition, VocabularyTerm
from src.app.modules.vocabulary.domain.exceptions import DuplicateTermError
from src.app.modules.vocabulary.domain.interfaces import VocabularyRepository

logger = structlog.get_logger().bind(module="vocabulary_service")


class ImportResult(TypedDict):
    imported_count: int
    review_count: int
    duplicates_skipped: int
    errors: list[dict]


class PaginatedTerms(TypedDict):
    items: list[VocabularyTerm]
    total: int
    page: int
    page_size: int
    has_next: bool


class SearchResult(TypedDict):
    term: VocabularyTerm
    highlight: str | None


class VocabularyService:
    def __init__(self, repository: VocabularyRepository) -> None:
        self._repo = repository

    async def list_terms(
        self,
        *,
        page: int = 1,
        page_size: int = 20,
        cefr_level: str | None = None,
        jlpt_level: str | None = None,
        parent_id: int | None = None,
    ) -> PaginatedTerms:
        offset = (page - 1) * page_size
        items, total = await self._repo.list_terms(
            page=page,
            page_size=page_size,
            cefr_level=cefr_level,
            jlpt_level=jlpt_level,
            parent_id=parent_id,
        )

        if items and not items[0].definitions:
            term_ids = [t.id for t in items if t.id is not None]
            if term_ids:
                definitions = await self._repo._load_definitions(term_ids)
                for item in items:
                    if item.id is not None:
                        item.definitions = definitions.get(item.id, [])

        has_next = offset + page_size < total
        return PaginatedTerms(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
            has_next=has_next,
        )

    async def search_terms(
        self,
        query: str,
        language: str | None = None,
        limit: int = 20,
    ) -> list[SearchResult]:
        terms = await self._repo.search_terms(query, language=language, limit=limit)
        results: list[SearchResult] = []

        if terms:
            term_ids = [t.id for t in terms if t.id is not None]
            if term_ids:
                definitions = await self._repo._load_definitions(term_ids)
                for term in terms:
                    if term.id is not None:
                        term.definitions = definitions.get(term.id, [])

        for term in terms:
            results.append(SearchResult(term=term, highlight=None))

        return results

    async def get_children(self, parent_id: int | None) -> list[VocabularyTerm]:
        children = await self._repo.get_children(parent_id)

        if children:
            term_ids = [t.id for t in children if t.id is not None]
            if term_ids:
                definitions = await self._repo._load_definitions(term_ids)
                for child in children:
                    if child.id is not None:
                        child.definitions = definitions.get(child.id, [])

        return children

    async def get_term_by_id(self, term_id: int | None) -> VocabularyTerm | None:
        if term_id is None:
            return None
        return await self._repo.get_term_by_id(term_id)

    async def create_user_term(
        self,
        *,
        term: str,
        language: str,
        definition: str | None = None,
        cefr_level: str | None = None,
        jlpt_level: str | None = None,
        part_of_speech: str | None = None,
        user_id: int | None = None,
    ) -> VocabularyTerm:
        existing = await self._repo.find_by_user_and_term(term, language, user_id=user_id)
        if existing is not None:
            raise DuplicateTermError()

        term_entity = VocabularyTerm(
            term=term,
            language=language,
            cefr_level=cefr_level,
            jlpt_level=jlpt_level,
            part_of_speech=part_of_speech,
        )
        created_term = await self._repo.create_term(term_entity)

        if definition is not None:
            definition_entity = VocabularyDefinition(
                term_id=created_term.id,
                language=language,
                definition=definition,
                source="user",
            )
            await self._repo.create_definition(definition_entity)

        import redis.asyncio as redis

        from src.app.core.config import settings
        from src.app.workers.enrichment_worker import enqueue_enrichment_job

        try:
            redis_client = redis.from_url(settings.redis_url)
            await enqueue_enrichment_job(
                redis_pool=redis_client,
                term=term,
                language=language,
                level=cefr_level or "A2",
                user_id=user_id,
                term_id=created_term.id,
            )
            await redis_client.aclose()
        except Exception as e:
            logger.warning("enrichment_job_enqueue_failed", term=term, error=str(e))

        loaded_term = await self._repo.get_term_by_id(created_term.id)
        if loaded_term is None:
            raise RuntimeError("Failed to reload created term")
        return loaded_term

    async def bulk_add_to_user_vocabulary(self, term_ids: list[int]) -> tuple[int, int]:
        added = 0
        skipped = 0
        for term_id in term_ids:
            term = await self._repo.get_term_by_id(term_id)
            if not term:
                continue
            existing = await self._repo.find_by_user_and_term(term.term, term.language)
            if existing:
                skipped += 1
            else:
                await self._repo.create_term(term)
                added += 1
        return added, skipped

    async def import_csv(self, parse_result: ParseResult) -> ImportResult:
        imported_count = 0
        review_count = 0
        duplicates_skipped = 0
        errors: list[dict] = []

        valid_rows = [row for row in parse_result.rows if row.status == "valid"]

        for i in range(0, len(valid_rows), 500):
            chunk = valid_rows[i : i + 500]
            terms = []
            for row in chunk:
                term = VocabularyTerm(
                    term=row.term or "",
                    language=row.language or "en",
                    cefr_level=row.cefr_level,
                    jlpt_level=row.jlpt_level,
                    part_of_speech=row.part_of_speech,
                )
                if row.definition:
                    term.definitions = [
                        VocabularyDefinition(
                            term_id=None,
                            language=row.language or "en",
                            definition=row.definition,
                            source="csv_import",
                        )
                    ]
                terms.append(term)

            try:
                persisted = await self._repo.bulk_create_terms(terms)
                imported_count += len(persisted)
            except Exception as e:
                for row in chunk:
                    errors.append({"row": row.row_number, "error": str(e)})

        for row in parse_result.rows:
            if row.status == "error":
                review_count += 1
            elif row.status == "warning":
                review_count += 1

        import redis.asyncio as redis

        from src.app.core.config import settings
        from src.app.workers.enrichment_worker import enqueue_enrichment_job

        try:
            redis_client = redis.from_url(settings.redis_url)
            for row in parse_result.rows:
                if row.status == "valid" and row.term:
                    level = row.cefr_level or row.jlpt_level or "A2"
                    await enqueue_enrichment_job(
                        redis_pool=redis_client,
                        term=row.term,
                        language=row.language or "en",
                        level=level,
                    )
            await redis_client.aclose()
        except Exception as e:
            logger.warning("csv_enrichment_jobs_enqueue_failed", error=str(e))

        return ImportResult(
            imported_count=imported_count,
            review_count=review_count,
            duplicates_skipped=duplicates_skipped,
            errors=errors,
        )
