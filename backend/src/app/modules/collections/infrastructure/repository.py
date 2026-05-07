import structlog
from sqlalchemy import and_, case, func, or_, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

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
from src.app.modules.collections.infrastructure.models import CollectionModel, CollectionTermModel
from src.app.modules.srs.infrastructure.models import SrsCardModel
from src.app.modules.vocabulary.infrastructure.models import VocabularyTermModel

logger = structlog.get_logger().bind(module="collections_repository")

DUPLICATE_COLLECTION_CONSTRAINT = "uq_collections_user_id_name"
DUPLICATE_COLLECTION_TERM_CONSTRAINT = "uq_collection_terms_collection_id_term_id"
MASTERY_STABILITY_THRESHOLD = 21.0


def _to_domain(model: CollectionModel) -> Collection:
    return Collection(
        id=model.id,
        user_id=model.user_id,
        name=model.name,
        icon=model.icon,
        created_at=model.created_at,
        updated_at=model.updated_at,
    )


class SqlAlchemyCollectionRepository(CollectionRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, collection: Collection) -> Collection:
        model = CollectionModel(
            user_id=collection.user_id,
            name=collection.name,
            icon=collection.icon,
        )
        self._session.add(model)
        try:
            await self._session.commit()
        except IntegrityError as exc:
            await self._session.rollback()
            if DUPLICATE_COLLECTION_CONSTRAINT in str(exc.orig):
                msg = "Collection name already exists for this user"
                raise DuplicateCollectionError(msg) from exc
            raise

        await self._session.refresh(model)
        logger.info("collection_row_created", user_id=model.user_id, collection_id=model.id)
        return _to_domain(model)

    async def get_by_id(self, collection_id: int, user_id: int) -> Collection | None:
        result = await self._session.execute(
            select(CollectionModel).where(
                CollectionModel.id == collection_id,
                CollectionModel.user_id == user_id,
            ),
        )
        model = result.scalar_one_or_none()
        if model is None:
            return None

        return _to_domain(model)

    async def list_by_user(self, user_id: int) -> list[Collection]:
        result = await self._session.execute(
            select(CollectionModel)
            .where(CollectionModel.user_id == user_id)
            .order_by(CollectionModel.updated_at.desc(), CollectionModel.id.desc()),
        )
        return [_to_domain(model) for model in result.scalars().all()]

    async def update(self, collection: Collection) -> Collection:
        if collection.id is None:
            msg = "Collection id is required for updates"
            raise CollectionNotFoundError(msg)

        result = await self._session.execute(
            select(CollectionModel).where(
                CollectionModel.id == collection.id,
                CollectionModel.user_id == collection.user_id,
            ),
        )
        model = result.scalar_one_or_none()
        if model is None:
            msg = "Collection not found"
            raise CollectionNotFoundError(
                msg,
                details={"collection_id": collection.id, "user_id": collection.user_id},
            )

        model.name = collection.name
        model.icon = collection.icon

        try:
            await self._session.commit()
        except IntegrityError as exc:
            await self._session.rollback()
            if DUPLICATE_COLLECTION_CONSTRAINT in str(exc.orig):
                msg = "Collection name already exists for this user"
                raise DuplicateCollectionError(msg) from exc
            raise

        await self._session.refresh(model)
        logger.info("collection_row_updated", user_id=model.user_id, collection_id=model.id)
        return _to_domain(model)

    async def delete(self, collection_id: int, user_id: int) -> None:
        result = await self._session.execute(
            select(CollectionModel).where(
                CollectionModel.id == collection_id,
                CollectionModel.user_id == user_id,
            ),
        )
        model = result.scalar_one_or_none()
        if model is None:
            msg = "Collection not found"
            raise CollectionNotFoundError(
                msg,
                details={"collection_id": collection_id, "user_id": user_id},
            )

        await self._session.delete(model)
        await self._session.commit()
        logger.info("collection_row_deleted", user_id=user_id, collection_id=collection_id)

    async def get_term_count(self, collection_id: int) -> int:
        result = await self._session.execute(
            select(func.count(CollectionTermModel.id)).where(
                CollectionTermModel.collection_id == collection_id,
            ),
        )
        return int(result.scalar_one() or 0)

    async def get_mastery_percent(self, collection_id: int, user_id: int) -> int:
        total_terms = await self.get_term_count(collection_id)
        if total_terms == 0:
            return 0

        result = await self._session.execute(
            select(func.count(SrsCardModel.id))
            .select_from(CollectionTermModel)
            .join(SrsCardModel, CollectionTermModel.term_id == SrsCardModel.term_id)
            .where(
                CollectionTermModel.collection_id == collection_id,
                SrsCardModel.user_id == user_id,
                SrsCardModel.stability.is_not(None),
                SrsCardModel.stability >= MASTERY_STABILITY_THRESHOLD,
            ),
        )
        mastered_terms = int(result.scalar_one() or 0)
        return round((mastered_terms / total_terms) * 100)


class SqlAlchemyCollectionTermRepository(CollectionTermRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add_term(self, collection_id: int, term_id: int) -> None:
        self._session.add(CollectionTermModel(collection_id=collection_id, term_id=term_id))
        try:
            await self._session.commit()
        except IntegrityError as exc:
            await self._session.rollback()
            if DUPLICATE_COLLECTION_TERM_CONSTRAINT in str(exc.orig):
                msg = "Term already exists in this collection"
                raise TermAlreadyInCollectionError(msg) from exc
            raise

        logger.info(
            "collection_term_row_created",
            collection_id=collection_id,
            term_id=term_id,
        )

    async def add_terms_bulk(self, collection_id: int, term_ids: list[int]) -> int:
        unique_term_ids = list(dict.fromkeys(term_ids))
        if not unique_term_ids:
            return 0

        result = await self._session.execute(
            insert(CollectionTermModel)
            .values(
                [
                    {"collection_id": collection_id, "term_id": term_id}
                    for term_id in unique_term_ids
                ]
            )
            .on_conflict_do_nothing(index_elements=["collection_id", "term_id"])
            .returning(CollectionTermModel.id),
        )
        inserted_count = len(result.scalars().all())
        await self._session.commit()

        logger.info(
            "collection_terms_bulk_created",
            collection_id=collection_id,
            inserted_count=inserted_count,
            requested_count=len(unique_term_ids),
        )
        return inserted_count

    async def remove_term(self, collection_id: int, term_id: int) -> None:
        result = await self._session.execute(
            select(CollectionTermModel).where(
                CollectionTermModel.collection_id == collection_id,
                CollectionTermModel.term_id == term_id,
            ),
        )
        model = result.scalar_one_or_none()
        if model is None:
            msg = "Term is not part of this collection"
            raise TermNotInCollectionError(
                msg,
                details={"collection_id": collection_id, "term_id": term_id},
            )

        await self._session.delete(model)
        await self._session.commit()

        logger.info(
            "collection_term_row_deleted",
            collection_id=collection_id,
            term_id=term_id,
        )

    async def term_exists_in_collection(self, collection_id: int, term_id: int) -> bool:
        result = await self._session.execute(
            select(func.count(CollectionTermModel.id)).where(
                CollectionTermModel.collection_id == collection_id,
                CollectionTermModel.term_id == term_id,
            ),
        )
        return bool(result.scalar_one())

    async def get_terms_by_collection(
        self,
        collection_id: int,
        user_id: int,
        page: int,
        page_size: int,
        search: str | None = None,
        mastery_status: str | None = None,
    ) -> tuple[list[CollectionTermEntry], int]:
        offset = (page - 1) * page_size
        mastery_expr = case(
            (SrsCardModel.id.is_(None), "new"),
            (
                and_(
                    SrsCardModel.stability.is_not(None),
                    SrsCardModel.stability >= MASTERY_STABILITY_THRESHOLD,
                ),
                "mastered",
            ),
            else_="learning",
        ).label("mastery_status")

        base_query = (
            select(VocabularyTermModel, CollectionTermModel.added_at, mastery_expr)
            .join(
                VocabularyTermModel,
                CollectionTermModel.term_id == VocabularyTermModel.id,
            )
            .outerjoin(
                SrsCardModel,
                and_(
                    SrsCardModel.term_id == VocabularyTermModel.id,
                    SrsCardModel.user_id == user_id,
                    SrsCardModel.language == VocabularyTermModel.language,
                ),
            )
            .where(CollectionTermModel.collection_id == collection_id)
        )

        if search is not None and search.strip():
            base_query = base_query.where(VocabularyTermModel.term.ilike(f"%{search.strip()}%"))

        count_query = (
            select(func.count(CollectionTermModel.id))
            .join(
                VocabularyTermModel,
                CollectionTermModel.term_id == VocabularyTermModel.id,
            )
            .outerjoin(
                SrsCardModel,
                and_(
                    SrsCardModel.term_id == VocabularyTermModel.id,
                    SrsCardModel.user_id == user_id,
                    SrsCardModel.language == VocabularyTermModel.language,
                ),
            )
            .where(CollectionTermModel.collection_id == collection_id)
        )

        if search is not None and search.strip():
            count_query = count_query.where(VocabularyTermModel.term.ilike(f"%{search.strip()}%"))

        if mastery_status is not None:
            if mastery_status == "new":
                base_query = base_query.where(SrsCardModel.id.is_(None))
                count_query = count_query.where(SrsCardModel.id.is_(None))
            elif mastery_status == "mastered":
                base_query = base_query.where(
                    and_(
                        SrsCardModel.stability.is_not(None),
                        SrsCardModel.stability >= MASTERY_STABILITY_THRESHOLD,
                    )
                )
                count_query = count_query.where(
                    and_(
                        SrsCardModel.stability.is_not(None),
                        SrsCardModel.stability >= MASTERY_STABILITY_THRESHOLD,
                    )
                )
            elif mastery_status == "learning":
                base_query = base_query.where(
                    and_(
                        SrsCardModel.id.is_not(None),
                        or_(
                            SrsCardModel.stability.is_(None),
                            SrsCardModel.stability < MASTERY_STABILITY_THRESHOLD,
                        ),
                    )
                )
                count_query = count_query.where(
                    and_(
                        SrsCardModel.id.is_not(None),
                        or_(
                            SrsCardModel.stability.is_(None),
                            SrsCardModel.stability < MASTERY_STABILITY_THRESHOLD,
                        ),
                    )
                )

        result = await self._session.execute(
            base_query.order_by(CollectionTermModel.added_at.desc(), CollectionTermModel.id.desc())
            .offset(offset)
            .limit(page_size),
        )
        count_result = await self._session.execute(count_query)

        items = [
            CollectionTermEntry(
                term_id=model.id,
                term=model.term,
                language=model.language,
                mastery_status=status,
                added_at=added_at,
                cefr_level=model.cefr_level,
                jlpt_level=model.jlpt_level,
                part_of_speech=model.part_of_speech,
            )
            for model, added_at, status in result.all()
        ]
        total = int(count_result.scalar_one() or 0)
        return items, total
