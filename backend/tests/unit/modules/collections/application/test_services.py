from datetime import UTC, datetime

import pytest

from src.app.modules.collections.application.services import CollectionService
from src.app.modules.collections.domain.entities import Collection, CollectionTermEntry
from src.app.modules.collections.domain.exceptions import (
    CollectionNotFoundError,
    DuplicateCollectionError,
    TermAlreadyInCollectionError,
    TermNotInCollectionError,
)
from src.app.modules.collections.domain.interfaces import (
    CollectionRepository,
    CollectionTermRepository,
)
from src.app.modules.vocabulary.domain.entities import VocabularyTerm


class InMemoryCollectionRepository(CollectionRepository):
    def __init__(self) -> None:
        self._collections: dict[int, Collection] = {}
        self._next_id = 1
        self._term_counts: dict[int, int] = {}
        self._mastery: dict[int, int] = {}

    def _copy_collection(self, collection: Collection) -> Collection:
        return Collection(
            id=collection.id,
            user_id=collection.user_id,
            name=collection.name,
            icon=collection.icon,
            term_count=collection.term_count,
            mastery_percent=collection.mastery_percent,
            created_at=collection.created_at,
            updated_at=collection.updated_at,
        )

    async def create(self, collection: Collection) -> Collection:
        for existing in self._collections.values():
            if existing.user_id == collection.user_id and existing.name == collection.name:
                msg = "Collection name already exists for this user"
                raise DuplicateCollectionError(msg)

        stored = Collection(
            id=self._next_id,
            user_id=collection.user_id,
            name=collection.name,
            icon=collection.icon,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )
        self._collections[self._next_id] = stored
        self._term_counts[self._next_id] = 0
        self._mastery[self._next_id] = 0
        self._next_id += 1
        return stored

    async def get_by_id(self, collection_id: int, user_id: int) -> Collection | None:
        collection = self._collections.get(collection_id)
        if collection is None or collection.user_id != user_id:
            return None
        return self._copy_collection(collection)

    async def list_by_user(self, user_id: int) -> list[Collection]:
        items = [
            collection
            for collection in self._collections.values()
            if collection.user_id == user_id
        ]
        return [self._copy_collection(collection) for collection in items]

    async def update(self, collection: Collection) -> Collection:
        if collection.id is None or collection.id not in self._collections:
            msg = "Collection not found"
            raise CollectionNotFoundError(msg)

        for existing in self._collections.values():
            if (
                existing.id != collection.id
                and existing.user_id == collection.user_id
                and existing.name == collection.name
            ):
                msg = "Collection name already exists for this user"
                raise DuplicateCollectionError(msg)

        stored = Collection(
            id=collection.id,
            user_id=collection.user_id,
            name=collection.name,
            icon=collection.icon,
            created_at=self._collections[collection.id].created_at,
            updated_at=datetime.now(UTC),
        )
        self._collections[collection.id] = stored
        return stored

    async def delete(self, collection_id: int, user_id: int) -> None:
        collection = self._collections.get(collection_id)
        if collection is None or collection.user_id != user_id:
            msg = "Collection not found"
            raise CollectionNotFoundError(msg)
        del self._collections[collection_id]
        self._term_counts.pop(collection_id, None)
        self._mastery.pop(collection_id, None)

    async def get_term_count(self, collection_id: int) -> int:
        return self._term_counts.get(collection_id, 0)

    async def get_mastery_percent(self, collection_id: int, user_id: int) -> int:
        _ = user_id
        return self._mastery.get(collection_id, 0)

    def set_metrics(self, collection_id: int, *, term_count: int, mastery_percent: int) -> None:
        self._term_counts[collection_id] = term_count
        self._mastery[collection_id] = mastery_percent


class InMemoryVocabularyRepository:
    def __init__(self) -> None:
        self._terms: dict[int, VocabularyTerm] = {}

    def add_term(
        self,
        *,
        term_id: int,
        term: str,
        language: str = "en",
        cefr_level: str | None = None,
        jlpt_level: str | None = None,
        part_of_speech: str | None = None,
    ) -> None:
        self._terms[term_id] = VocabularyTerm(
            id=term_id,
            term=term,
            language=language,
            cefr_level=cefr_level,
            jlpt_level=jlpt_level,
            part_of_speech=part_of_speech,
        )

    async def get_term_by_id(self, term_id: int | None) -> VocabularyTerm | None:
        if term_id is None:
            return None
        return self._terms.get(term_id)

    async def find_by_value(self, term: str, language: str) -> VocabularyTerm | None:
        for item in self._terms.values():
            if item.term == term and item.language == language:
                return item
        return None


class InMemoryCollectionTermRepository(CollectionTermRepository):
    def __init__(self, vocabulary_repository: InMemoryVocabularyRepository) -> None:
        self._vocabulary_repository = vocabulary_repository
        self._terms_by_collection: dict[int, list[int]] = {}
        self._mastery_status_by_term_id: dict[int, str] = {}

    async def add_term(self, collection_id: int, term_id: int) -> None:
        term_ids = self._terms_by_collection.setdefault(collection_id, [])
        if term_id in term_ids:
            msg = "Term already exists in this collection"
            raise TermAlreadyInCollectionError(msg)
        term_ids.append(term_id)

    async def add_terms_bulk(self, collection_id: int, term_ids: list[int]) -> int:
        inserted = 0
        for term_id in dict.fromkeys(term_ids):
            if await self.term_exists_in_collection(collection_id, term_id):
                continue
            self._terms_by_collection.setdefault(collection_id, []).append(term_id)
            inserted += 1
        return inserted

    async def remove_term(self, collection_id: int, term_id: int) -> None:
        term_ids = self._terms_by_collection.get(collection_id, [])
        if term_id not in term_ids:
            msg = "Term is not part of this collection"
            raise TermNotInCollectionError(msg)
        self._terms_by_collection[collection_id] = [
            value for value in term_ids if value != term_id
        ]

    async def term_exists_in_collection(self, collection_id: int, term_id: int) -> bool:
        return term_id in self._terms_by_collection.get(collection_id, [])

    async def get_terms_by_collection(
        self,
        collection_id: int,
        user_id: int,
        page: int,
        page_size: int,
    ) -> tuple[list[CollectionTermEntry], int]:
        _ = user_id
        term_ids = self._terms_by_collection.get(collection_id, [])
        offset = (page - 1) * page_size
        paged_ids = term_ids[offset : offset + page_size]

        items: list[CollectionTermEntry] = []
        for term_id in paged_ids:
            term = await self._vocabulary_repository.get_term_by_id(term_id)
            if term is None:
                continue
            items.append(
                CollectionTermEntry(
                    term_id=term_id,
                    term=term.term,
                    language=term.language,
                    mastery_status=self._mastery_status_by_term_id.get(term_id, "new"),
                    cefr_level=term.cefr_level,
                    jlpt_level=term.jlpt_level,
                    part_of_speech=term.part_of_speech,
                )
            )
        return items, len(term_ids)

    def set_mastery_status(self, term_id: int, status: str) -> None:
        self._mastery_status_by_term_id[term_id] = status


async def test_collection_service_create_collection_returns_enriched_collection() -> None:
    repository = InMemoryCollectionRepository()
    vocabulary_repository = InMemoryVocabularyRepository()
    term_repository = InMemoryCollectionTermRepository(vocabulary_repository)
    service = CollectionService(repository, term_repository, vocabulary_repository)

    created = await service.create_collection(user_id=7, name="TOEIC", icon="📚")

    assert created.id == 1
    assert created.user_id == 7
    assert created.name == "TOEIC"
    assert created.icon == "📚"
    assert created.term_count == 0
    assert created.mastery_percent == 0


async def test_collection_service_list_collections_includes_term_count_and_mastery() -> None:
    repository = InMemoryCollectionRepository()
    vocabulary_repository = InMemoryVocabularyRepository()
    term_repository = InMemoryCollectionTermRepository(vocabulary_repository)
    service = CollectionService(repository, term_repository, vocabulary_repository)

    first = await service.create_collection(user_id=7, name="Networking", icon="🌍")
    second = await service.create_collection(user_id=7, name="Backend", icon="💻")
    repository.set_metrics(first.id or 0, term_count=4, mastery_percent=25)
    repository.set_metrics(second.id or 0, term_count=6, mastery_percent=50)

    collections = await service.list_collections(user_id=7)

    assert len(collections) == 2
    assert {
        (collection.name, collection.term_count, collection.mastery_percent)
        for collection in collections
    } == {
        ("Networking", 4, 25),
        ("Backend", 6, 50),
    }


async def test_collection_service_updates_collection_name() -> None:
    repository = InMemoryCollectionRepository()
    vocabulary_repository = InMemoryVocabularyRepository()
    term_repository = InMemoryCollectionTermRepository(vocabulary_repository)
    service = CollectionService(repository, term_repository, vocabulary_repository)

    created = await service.create_collection(user_id=7, name="Exam Prep", icon="🎯")
    updated = await service.update_collection(
        collection_id=created.id or 0,
        user_id=7,
        name="Exam Review",
    )

    assert updated.name == "Exam Review"
    assert updated.icon == "🎯"


async def test_collection_service_delete_collection_removes_only_target_collection() -> None:
    repository = InMemoryCollectionRepository()
    vocabulary_repository = InMemoryVocabularyRepository()
    term_repository = InMemoryCollectionTermRepository(vocabulary_repository)
    service = CollectionService(repository, term_repository, vocabulary_repository)

    first = await service.create_collection(user_id=7, name="Work", icon="💼")
    second = await service.create_collection(user_id=7, name="Travel", icon="✈️")

    await service.delete_collection(collection_id=first.id or 0, user_id=7)

    remaining = await service.list_collections(user_id=7)
    assert [collection.name for collection in remaining] == [second.name]


async def test_collection_service_get_collection_raises_not_found_for_missing_record() -> None:
    repository = InMemoryCollectionRepository()
    vocabulary_repository = InMemoryVocabularyRepository()
    term_repository = InMemoryCollectionTermRepository(vocabulary_repository)
    service = CollectionService(repository, term_repository, vocabulary_repository)

    with pytest.raises(CollectionNotFoundError):
        await service.get_collection(collection_id=999, user_id=7)


async def test_collection_service_add_term_to_collection_rejects_duplicates() -> None:
    repository = InMemoryCollectionRepository()
    vocabulary_repository = InMemoryVocabularyRepository()
    vocabulary_repository.add_term(term_id=101, term="protocol", cefr_level="B2")
    term_repository = InMemoryCollectionTermRepository(vocabulary_repository)
    service = CollectionService(repository, term_repository, vocabulary_repository)

    collection = await service.create_collection(user_id=7, name="Backend", icon="💻")
    await service.add_term_to_collection(user_id=7, collection_id=collection.id or 0, term_id=101)

    with pytest.raises(TermAlreadyInCollectionError):
        await service.add_term_to_collection(
            user_id=7, collection_id=collection.id or 0, term_id=101
        )


async def test_collection_service_add_terms_bulk_counts_added_and_skipped() -> None:
    repository = InMemoryCollectionRepository()
    vocabulary_repository = InMemoryVocabularyRepository()
    vocabulary_repository.add_term(term_id=101, term="protocol")
    vocabulary_repository.add_term(term_id=102, term="deploy")
    vocabulary_repository.add_term(term_id=103, term="latency")
    term_repository = InMemoryCollectionTermRepository(vocabulary_repository)
    service = CollectionService(repository, term_repository, vocabulary_repository)

    collection = await service.create_collection(user_id=7, name="Infra", icon="⚙️")
    await service.add_term_to_collection(user_id=7, collection_id=collection.id or 0, term_id=101)

    result = await service.add_terms_bulk(
        user_id=7,
        collection_id=collection.id or 0,
        term_ids=[101, 102, 102, 103],
    )

    assert result == {"added": 2, "skipped": 2}


async def test_collection_service_get_collection_terms_supports_mastery_and_pagination() -> None:
    repository = InMemoryCollectionRepository()
    vocabulary_repository = InMemoryVocabularyRepository()
    vocabulary_repository.add_term(term_id=101, term="protocol", cefr_level="B2")
    vocabulary_repository.add_term(term_id=102, term="deploy", part_of_speech="verb")
    term_repository = InMemoryCollectionTermRepository(vocabulary_repository)
    term_repository.set_mastery_status(101, "mastered")
    term_repository.set_mastery_status(102, "learning")
    service = CollectionService(repository, term_repository, vocabulary_repository)

    collection = await service.create_collection(user_id=7, name="Backend", icon="💻")
    await service.add_terms_bulk(
        user_id=7,
        collection_id=collection.id or 0,
        term_ids=[101, 102],
    )

    result = await service.get_collection_terms(
        user_id=7,
        collection_id=collection.id or 0,
        page=1,
        page_size=1,
    )

    assert result["total"] == 2
    assert result["has_next"] is True
    assert result["items"][0].mastery_status == "mastered"


async def test_collection_service_import_csv_skips_duplicates() -> None:
    repository = InMemoryCollectionRepository()
    vocabulary_repository = InMemoryVocabularyRepository()
    vocabulary_repository.add_term(term_id=101, term="protocol")
    vocabulary_repository.add_term(term_id=102, term="deploy")
    term_repository = InMemoryCollectionTermRepository(vocabulary_repository)
    service = CollectionService(repository, term_repository, vocabulary_repository)

    collection = await service.create_collection(user_id=7, name="CSV", icon="📚")
    csv_content = b"term,language\nprotocol,en\ndeploy,en\nprotocol,en\nmissing,en\n"

    result = await service.import_csv_to_collection(
        user_id=7,
        collection_id=collection.id or 0,
        file_content=csv_content,
    )

    assert result["added"] == 2
    assert result["skipped"] == 1
    assert result["errors"] == [{"row": 4, "error": 'Term "missing" was not found in the corpus'}]


async def test_collection_service_remove_term_keeps_vocabulary_term() -> None:
    repository = InMemoryCollectionRepository()
    vocabulary_repository = InMemoryVocabularyRepository()
    vocabulary_repository.add_term(term_id=101, term="protocol")
    term_repository = InMemoryCollectionTermRepository(vocabulary_repository)
    service = CollectionService(repository, term_repository, vocabulary_repository)

    collection = await service.create_collection(user_id=7, name="Backend", icon="💻")
    await service.add_term_to_collection(user_id=7, collection_id=collection.id or 0, term_id=101)

    await service.remove_term_from_collection(
        user_id=7,
        collection_id=collection.id or 0,
        term_id=101,
    )

    assert await term_repository.term_exists_in_collection(collection.id or 0, 101) is False
    assert await vocabulary_repository.get_term_by_id(101) is not None


async def test_collection_service_enforces_collection_ownership_for_term_changes() -> None:
    repository = InMemoryCollectionRepository()
    vocabulary_repository = InMemoryVocabularyRepository()
    vocabulary_repository.add_term(term_id=101, term="protocol")
    term_repository = InMemoryCollectionTermRepository(vocabulary_repository)
    service = CollectionService(repository, term_repository, vocabulary_repository)

    collection = await service.create_collection(user_id=7, name="Private", icon="🔒")

    with pytest.raises(CollectionNotFoundError):
        await service.add_term_to_collection(
            user_id=99, collection_id=collection.id or 0, term_id=101
        )
