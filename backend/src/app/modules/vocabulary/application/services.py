from typing import TypedDict

from src.app.modules.vocabulary.domain.entities import VocabularyDefinition, VocabularyTerm
from src.app.modules.vocabulary.domain.interfaces import VocabularyRepository


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
