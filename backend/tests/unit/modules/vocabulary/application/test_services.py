
from src.app.modules.vocabulary.application.services import VocabularyService
from src.app.modules.vocabulary.domain.entities import VocabularyDefinition, VocabularyTerm
from src.app.modules.vocabulary.domain.interfaces import VocabularyRepository


class InMemoryVocabularyRepository(VocabularyRepository):
    def __init__(self) -> None:
        self._terms: dict[int, VocabularyTerm] = {}
        self._definitions: dict[int, list[VocabularyDefinition]] = {}
        self._next_id = 1

    async def create_term(self, term: VocabularyTerm) -> VocabularyTerm:
        term.id = self._next_id
        self._next_id += 1
        self._terms[term.id] = term
        self._definitions[term.id] = term.definitions.copy()
        return term

    async def create_definition(self, definition: VocabularyDefinition) -> VocabularyDefinition:
        if definition.term_id is None:
            msg = "Definition term_id is required"
            raise ValueError(msg)
        self._definitions.setdefault(definition.term_id, []).append(definition)
        return definition

    async def get_term_by_id(self, term_id: int | None) -> VocabularyTerm | None:
        if term_id is None:
            return None
        term = self._terms.get(term_id)
        if term is None:
            return None
        term.definitions = self._definitions.get(term_id, []).copy()
        return term

    async def search_terms(
        self,
        query: str,
        *,
        language: str | None = None,
        limit: int = 20,
    ) -> list[VocabularyTerm]:
        results = [
            term
            for term in self._terms.values()
            if query.lower() in term.term.lower()
            and (language is None or term.language == language)
        ]
        return results[:limit]

    async def get_children(self, parent_id: int | None) -> list[VocabularyTerm]:
        return [term for term in self._terms.values() if term.parent_id == parent_id]

    async def bulk_create_terms(self, terms: list[VocabularyTerm]) -> list[VocabularyTerm]:
        for term in terms:
            await self.create_term(term)
        return terms

    async def list_terms(
        self,
        *,
        page: int,
        page_size: int,
        cefr_level: str | None = None,
        jlpt_level: str | None = None,
        parent_id: int | None = None,
    ) -> tuple[list[VocabularyTerm], int]:
        filtered = [
            term
            for term in self._terms.values()
            if (cefr_level is None or term.cefr_level == cefr_level)
            and (jlpt_level is None or term.jlpt_level == jlpt_level)
            and (parent_id is None or term.parent_id == parent_id)
        ]

        offset = (page - 1) * page_size
        page_items = sorted(filtered, key=lambda t: t.term)[offset : offset + page_size]

        for term in page_items:
            term.definitions = self._definitions.get(term.id or 0, []).copy()

        return page_items, len(filtered)

    async def _load_definitions(
        self,
        term_ids: list[int],
    ) -> dict[int, list[VocabularyDefinition]]:
        return {tid: self._definitions.get(tid, []) for tid in term_ids}

    async def find_by_user_and_term(
        self,
        term: str,
        language: str,
        user_id: int | None = None,
    ) -> VocabularyTerm | None:
        for t in self._terms.values():
            if t.term == term and t.language == language:
                return t
        return None

    async def find_by_value(self, term: str, language: str) -> VocabularyTerm | None:
        for t in self._terms.values():
            if t.term == term and t.language == language:
                return t
        return None


async def test_vocabulary_service_list_terms_pagination() -> None:
    repo = InMemoryVocabularyRepository()

    for i in range(25):
        term = VocabularyTerm(
            term=f"term_{i}",
            language="en",
            part_of_speech="noun",
        )
        await repo.create_term(term)

    service = VocabularyService(repo)

    result = await service.list_terms(page=1, page_size=10)

    assert len(result["items"]) == 10
    assert result["total"] == 25
    assert result["page"] == 1
    assert result["page_size"] == 10
    assert result["has_next"] is True


async def test_vocabulary_service_list_terms_filters() -> None:
    repo = InMemoryVocabularyRepository()

    for level in ["A1", "B1", "C1"]:
        term = VocabularyTerm(
            term=f"term_{level}",
            language="en",
            cefr_level=level,
            part_of_speech="noun",
        )
        await repo.create_term(term)

    service = VocabularyService(repo)

    result = await service.list_terms(cefr_level="B1")

    assert len(result["items"]) == 1
    assert result["items"][0].cefr_level == "B1"
    assert result["total"] == 1


async def test_vocabulary_service_list_terms_with_definitions() -> None:
    repo = InMemoryVocabularyRepository()

    term = VocabularyTerm(
        term="test",
        language="en",
        part_of_speech="noun",
    )
    created = await repo.create_term(term)
    await repo.create_definition(
        VocabularyDefinition(
            term_id=created.id,
            language="en",
            definition="A test definition",
            source="seed",
        ),
    )

    service = VocabularyService(repo)

    result = await service.list_terms(page=1, page_size=10)

    assert len(result["items"]) == 1
    assert len(result["items"][0].definitions) == 1
    assert result["items"][0].definitions[0].definition == "A test definition"


async def test_vocabulary_service_search_terms() -> None:
    repo = InMemoryVocabularyRepository()

    for text in ["apple", "application", "banana"]:
        await repo.create_term(
            VocabularyTerm(term=text, language="en", part_of_speech="noun"),
        )

    service = VocabularyService(repo)

    results = await service.search_terms("app")

    assert len(results) == 2
    assert all("app" in r["term"].term.lower() for r in results)


async def test_vocabulary_service_search_terms_with_language() -> None:
    repo = InMemoryVocabularyRepository()

    await repo.create_term(
        VocabularyTerm(term="hello", language="en", part_of_speech="noun"),
    )
    await repo.create_term(
        VocabularyTerm(term="konnichiwa", language="jp", part_of_speech="noun"),
    )

    service = VocabularyService(repo)

    results = await service.search_terms("hello", language="en")

    assert len(results) == 1
    assert results[0]["term"].language == "en"


async def test_vocabulary_service_get_children() -> None:
    repo = InMemoryVocabularyRepository()

    parent = await repo.create_term(
        VocabularyTerm(term="Parent", language="en", part_of_speech="noun"),
    )
    child1 = await repo.create_term(
        VocabularyTerm(term="Child1", language="en", parent_id=parent.id, part_of_speech="noun"),
    )
    child2 = await repo.create_term(
        VocabularyTerm(term="Child2", language="en", parent_id=parent.id, part_of_speech="noun"),
    )
    await repo.create_term(
        VocabularyTerm(term="Other", language="en", part_of_speech="noun"),
    )

    service = VocabularyService(repo)

    children = await service.get_children(parent.id)

    assert len(children) == 2
    assert {c.term for c in children} == {"Child1", "Child2"}


async def test_vocabulary_service_get_term_by_id() -> None:
    repo = InMemoryVocabularyRepository()

    term = await repo.create_term(
        VocabularyTerm(term="test term", language="en", part_of_speech="noun"),
    )
    await repo.create_definition(
        VocabularyDefinition(
            term_id=term.id,
            language="en",
            definition="Test definition",
            source="seed",
        ),
    )

    service = VocabularyService(repo)

    result = await service.get_term_by_id(term.id)

    assert result is not None
    assert result.term == "test term"
    assert len(result.definitions) == 1


async def test_vocabulary_service_get_term_by_id_not_found() -> None:
    repo = InMemoryVocabularyRepository()
    service = VocabularyService(repo)

    result = await service.get_term_by_id(9999)

    assert result is None
