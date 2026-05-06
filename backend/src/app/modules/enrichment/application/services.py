import redis.asyncio as redis
from sqlalchemy.ext.asyncio import AsyncSession

from src.app.llm.gateway import GatewayOrchestrator
from src.app.modules.enrichment.domain.interfaces import EnrichedTerm, EnrichmentServiceInterface
from src.app.modules.vocabulary.infrastructure.repository import VocabularyRepositoryImpl


class CorpusOnlyEnrichmentService(EnrichmentServiceInterface):
    def __init__(self, session: AsyncSession | None = None) -> None:
        self._session = session

    async def find_terms_for_request(
        self, topic: str, language: str, level: str, count: int
    ) -> list[EnrichedTerm]:
        if self._session is None:
            return []

        repo = VocabularyRepositoryImpl(self._session)
        terms = await repo.search_terms(topic, language=language, limit=count)

        if language == "jp":
            filtered = [t for t in terms if t.jlpt_level == level]
        else:
            filtered = [t for t in terms if t.cefr_level == level]

        results: list[EnrichedTerm] = []
        for term in filtered[:count]:
            first_def = term.definitions[0] if term.definitions else None
            results.append(
                EnrichedTerm(
                    term_id=term.id,
                    term=term.term,
                    language=term.language,
                    definition=first_def.definition if first_def else None,
                    ipa=first_def.ipa if first_def else None,
                    cefr_level=term.cefr_level,
                    jlpt_level=int(term.jlpt_level) if term.jlpt_level else None,
                    examples=list(first_def.examples) if first_def else [],
                    source="corpus",
                )
            )
        return results


class GatewayEnrichmentService(EnrichmentServiceInterface):
    def __init__(
        self,
        session: AsyncSession | None = None,
        redis_client: redis.Redis | None = None,
    ) -> None:
        self._session = session
        self._redis = redis_client

    def _level_matches(self, term: EnrichedTerm, language: str, level: str) -> bool:
        if language == "jp":
            return term.jlpt_level is not None and str(term.jlpt_level) == level
        return term.cefr_level == level

    async def find_terms_for_request(
        self, topic: str, language: str, level: str, count: int
    ) -> list[EnrichedTerm]:
        if self._session is None:
            return []

        repo = VocabularyRepositoryImpl(self._session)

        terms = await repo.search_terms(topic, language=language, limit=count * 2)
        filtered = [t for t in terms if self._level_matches(t, language, level)]

        corpus_terms: list[EnrichedTerm] = []
        for term in filtered[:count]:
            first_def = term.definitions[0] if term.definitions else None
            corpus_terms.append(
                EnrichedTerm(
                    term_id=term.id,
                    term=term.term,
                    language=term.language,
                    definition=first_def.definition if first_def else None,
                    ipa=first_def.ipa if first_def else None,
                    cefr_level=term.cefr_level,
                    jlpt_level=int(term.jlpt_level) if term.jlpt_level else None,
                    examples=list(first_def.examples) if first_def else [],
                    source="corpus",
                )
            )

        existing_ids = [t.term_id for t in corpus_terms if t.term_id is not None]
        gap_count = max(0, count - len(corpus_terms))

        if gap_count == 0 or self._redis is None:
            return corpus_terms[:count]

        orchestrator = GatewayOrchestrator(self._redis)

        preview_id, llm_candidates = await orchestrator.generate_preview_candidates(
            topic=topic,
            language=language,
            level=level,
            count=count,
            existing_term_ids=existing_ids,
        )

        all_terms = list(corpus_terms)
        for candidate in llm_candidates:
            all_terms.append(
                EnrichedTerm(
                    term_id=None,
                    term=candidate.term,
                    language=candidate.language,
                    definition=candidate.definition,
                    ipa=candidate.ipa,
                    cefr_level=candidate.cefr_level,
                    jlpt_level=candidate.jlpt_level,
                    examples=list(candidate.examples),
                    source="llm",
                    preview_id=preview_id,
                    validated_against_jmdict=candidate.validated_against_jmdict,
                )
            )

        return all_terms[:count]
