from typing import TypedDict

import structlog

from src.app.modules.collections.domain.entities import Collection, CollectionTermEntry
from src.app.modules.collections.domain.exceptions import (
    CollectionNotFoundError,
    TermAlreadyInCollectionError,
    VocabularyTermNotFoundError,
)
from src.app.modules.collections.domain.interfaces import (
    CollectionRepository,
    CollectionTermRepository,
)
from src.app.modules.vocabulary.application.csv_parser import parse_csv
from src.app.modules.vocabulary.domain.interfaces import VocabularyRepository

logger = structlog.get_logger().bind(module="collections_service")


class AddTermsResult(TypedDict):
    added: int
    skipped: int


class CollectionTermsPage(TypedDict):
    items: list[CollectionTermEntry]
    total: int
    page: int
    page_size: int
    has_next: bool


class CollectionCSVImportError(TypedDict):
    row: int
    error: str


class CollectionCSVImportResult(TypedDict):
    added: int
    skipped: int
    errors: list[CollectionCSVImportError]


class CollectionService:
    def __init__(
        self,
        repository: CollectionRepository,
        term_repository: CollectionTermRepository,
        vocabulary_repository: VocabularyRepository,
    ) -> None:
        self._repository = repository
        self._term_repository = term_repository
        self._vocabulary_repository = vocabulary_repository

    async def create_collection(self, *, user_id: int, name: str, icon: str) -> Collection:
        collection = await self._repository.create(
            Collection(user_id=user_id, name=name, icon=icon),
        )
        logger.info("collection_created", user_id=user_id, collection_id=collection.id)
        return await self._enrich_collection(collection)

    async def get_collection(self, *, collection_id: int, user_id: int) -> Collection:
        collection = await self._get_existing_collection(
            collection_id=collection_id, user_id=user_id
        )
        return await self._enrich_collection(collection)

    async def list_collections(self, *, user_id: int) -> list[Collection]:
        collections = await self._repository.list_by_user(user_id)
        return [await self._enrich_collection(collection) for collection in collections]

    async def update_collection(
        self,
        *,
        collection_id: int,
        user_id: int,
        name: str | None = None,
        icon: str | None = None,
    ) -> Collection:
        collection = await self._get_existing_collection(
            collection_id=collection_id, user_id=user_id
        )
        if name is not None:
            collection.name = name
        if icon is not None:
            collection.icon = icon

        updated = await self._repository.update(collection)
        logger.info("collection_updated", user_id=user_id, collection_id=updated.id)
        return await self._enrich_collection(updated)

    async def delete_collection(self, *, collection_id: int, user_id: int) -> None:
        await self._get_existing_collection(collection_id=collection_id, user_id=user_id)
        await self._repository.delete(collection_id, user_id)
        logger.info("collection_deleted", user_id=user_id, collection_id=collection_id)

    async def add_term_to_collection(
        self,
        *,
        user_id: int,
        collection_id: int,
        term_id: int,
    ) -> AddTermsResult:
        await self._get_existing_collection(collection_id=collection_id, user_id=user_id)
        await self._require_existing_term(term_id)

        if await self._term_repository.term_exists_in_collection(collection_id, term_id):
            msg = "Term already exists in this collection"
            raise TermAlreadyInCollectionError(
                msg,
                details={"collection_id": collection_id, "term_id": term_id},
            )

        await self._term_repository.add_term(collection_id, term_id)
        logger.info(
            "term_added_to_collection",
            user_id=user_id,
            collection_id=collection_id,
            term_id=term_id,
        )
        return AddTermsResult(added=1, skipped=0)

    async def add_terms_bulk(
        self,
        *,
        user_id: int,
        collection_id: int,
        term_ids: list[int],
    ) -> AddTermsResult:
        await self._get_existing_collection(collection_id=collection_id, user_id=user_id)

        unique_term_ids = list(dict.fromkeys(term_ids))
        skipped = len(term_ids) - len(unique_term_ids)
        insertable_term_ids: list[int] = []

        for term_id in unique_term_ids:
            await self._require_existing_term(term_id)
            if await self._term_repository.term_exists_in_collection(collection_id, term_id):
                skipped += 1
                continue
            insertable_term_ids.append(term_id)

        added = await self._term_repository.add_terms_bulk(collection_id, insertable_term_ids)
        skipped += len(insertable_term_ids) - added

        logger.info(
            "terms_bulk_added_to_collection",
            user_id=user_id,
            collection_id=collection_id,
            requested_count=len(term_ids),
            added_count=added,
            skipped_count=skipped,
        )
        return AddTermsResult(added=added, skipped=skipped)

    async def remove_term_from_collection(
        self,
        *,
        user_id: int,
        collection_id: int,
        term_id: int,
    ) -> None:
        await self._get_existing_collection(collection_id=collection_id, user_id=user_id)
        await self._term_repository.remove_term(collection_id, term_id)
        logger.info(
            "term_removed_from_collection",
            user_id=user_id,
            collection_id=collection_id,
            term_id=term_id,
        )

    async def get_collection_terms(
        self,
        *,
        user_id: int,
        collection_id: int,
        page: int,
        page_size: int,
        search: str | None = None,
        mastery_status: str | None = None,
    ) -> CollectionTermsPage:
        await self._get_existing_collection(collection_id=collection_id, user_id=user_id)
        items, total = await self._term_repository.get_terms_by_collection(
            collection_id,
            user_id,
            page,
            page_size,
            search=search,
            mastery_status=mastery_status,
        )
        has_next = (page * page_size) < total
        return CollectionTermsPage(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
            has_next=has_next,
        )

    async def import_csv_to_collection(
        self,
        *,
        user_id: int,
        collection_id: int,
        file_content: bytes,
    ) -> CollectionCSVImportResult:
        await self._get_existing_collection(collection_id=collection_id, user_id=user_id)

        parse_result = parse_csv(file_content)
        matched_term_ids: list[int] = []
        errors: list[CollectionCSVImportError] = []

        for row in parse_result.rows:
            if row.term is None:
                errors.append(
                    {
                        "row": row.row_number,
                        "error": row.error_message or "Missing required field: term",
                    }
                )
                continue

            if row.status == "error":
                errors.append(
                    {"row": row.row_number, "error": row.error_message or "Invalid CSV row"}
                )
                continue

            matched_term = await self._vocabulary_repository.find_by_value(
                row.term,
                row.language or "en",
            )
            if matched_term is None or matched_term.id is None:
                errors.append(
                    {
                        "row": row.row_number,
                        "error": f'Term "{row.term}" was not found in the corpus',
                    }
                )
                continue

            matched_term_ids.append(matched_term.id)

        unique_term_ids = list(dict.fromkeys(matched_term_ids))
        added = await self._term_repository.add_terms_bulk(collection_id, unique_term_ids)
        skipped = (len(matched_term_ids) - len(unique_term_ids)) + (len(unique_term_ids) - added)

        logger.info(
            "csv_import_to_collection",
            user_id=user_id,
            collection_id=collection_id,
            added_count=added,
            skipped_count=skipped,
            error_count=len(errors),
        )
        return CollectionCSVImportResult(added=added, skipped=skipped, errors=errors)

    async def _get_existing_collection(self, *, collection_id: int, user_id: int) -> Collection:
        collection = await self._repository.get_by_id(collection_id, user_id)
        if collection is None:
            msg = "Collection not found"
            raise CollectionNotFoundError(
                msg,
                details={"collection_id": collection_id, "user_id": user_id},
            )
        return collection

    async def _enrich_collection(self, collection: Collection) -> Collection:
        if collection.id is None:
            return collection

        collection.term_count = await self._repository.get_term_count(collection.id)
        collection.mastery_percent = await self._repository.get_mastery_percent(
            collection.id,
            collection.user_id,
        )
        return collection

    async def _require_existing_term(self, term_id: int) -> None:
        term = await self._vocabulary_repository.get_term_by_id(term_id)
        if term is not None:
            return

        msg = "Vocabulary term not found"
        raise VocabularyTermNotFoundError(msg, details={"term_id": term_id})
