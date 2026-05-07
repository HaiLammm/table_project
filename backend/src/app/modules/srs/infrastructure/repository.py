from datetime import datetime, timedelta
from math import ceil
from uuid import UUID

import structlog
from sqlalchemy import case, exists, func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from src.app.modules.collections.infrastructure.models import CollectionTermModel
from src.app.modules.srs.domain.entities import (
    DueCardsPage,
    DueCardWithTerm,
    EmbeddedTerm,
    QueueStats,
    Review,
    ScheduleBucket,
    SessionReviewRow,
    SrsCard,
    UpcomingSchedule,
)
from src.app.modules.srs.domain.exceptions import (
    CardNotFoundError,
    DuplicateCardError,
    NoReviewToUndoError,
)
from src.app.modules.srs.domain.interfaces import SrsCardRepository
from src.app.modules.srs.domain.value_objects import QueueMode, Rating
from src.app.modules.srs.infrastructure.models import SrsCardModel, SrsReviewModel
from src.app.modules.vocabulary.infrastructure.models import (
    VocabularyDefinitionModel,
    VocabularyTermModel,
)

logger = structlog.get_logger().bind(module="srs_repository")

DUPLICATE_CARD_CONSTRAINT = "uq_srs_cards_user_id_term_id_language"


def _to_domain(model: SrsCardModel) -> SrsCard:
    return SrsCard(
        id=model.id,
        user_id=model.user_id,
        term_id=model.term_id,
        language=model.language,
        due_at=model.due_at,
        fsrs_state=model.fsrs_state,
        stability=model.stability,
        difficulty=model.difficulty,
        reps=model.reps,
        lapses=model.lapses,
        created_at=model.created_at,
        updated_at=model.updated_at,
    )


def _review_to_domain(model: SrsReviewModel) -> Review:
    return Review(
        id=model.id,
        card_id=model.card_id,
        user_id=model.user_id,
        rating=Rating.from_score(model.rating),
        reviewed_at=model.reviewed_at,
        response_time_ms=model.response_time_ms,
        session_length_s=model.session_length_s,
        parallel_mode_active=model.parallel_mode_active,
        session_id=model.session_id,
        previous_fsrs_state=model.previous_fsrs_state,
        previous_stability=model.previous_stability,
        previous_difficulty=model.previous_difficulty,
        previous_reps=model.previous_reps,
        previous_lapses=model.previous_lapses,
    )


class SqlAlchemySrsCardRepository(SrsCardRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create_card(self, card: SrsCard) -> SrsCard:
        model = SrsCardModel(
            user_id=card.user_id,
            term_id=card.term_id,
            language=card.language,
            due_at=card.due_at,
            fsrs_state=card.fsrs_state,
            stability=card.stability,
            difficulty=card.difficulty,
            reps=card.reps,
            lapses=card.lapses,
        )
        self._session.add(model)
        try:
            await self._session.commit()
        except IntegrityError as exc:
            await self._session.rollback()
            if DUPLICATE_CARD_CONSTRAINT in str(exc.orig):
                msg = "Card already exists for this term and language"
                raise DuplicateCardError(msg) from exc
            raise

        await self._session.refresh(model)

        logger.info(
            "srs_card_created",
            user_id=model.user_id,
            term_id=model.term_id,
            language=model.language,
        )
        return _to_domain(model)

    async def update_card(self, card: SrsCard) -> SrsCard:
        if card.id is None:
            msg = "Card id is required for updates"
            raise CardNotFoundError(msg)

        result = await self._session.execute(
            select(SrsCardModel).where(
                SrsCardModel.id == card.id,
                SrsCardModel.user_id == card.user_id,
            ),
        )
        model = result.scalar_one_or_none()
        if model is None:
            msg = "Card not found"
            raise CardNotFoundError(msg)

        model.term_id = card.term_id
        model.language = card.language
        model.due_at = card.due_at
        model.fsrs_state = card.fsrs_state
        model.stability = card.stability
        model.difficulty = card.difficulty
        model.reps = card.reps
        model.lapses = card.lapses

        await self._session.commit()
        await self._session.refresh(model)

        logger.info("srs_card_updated", user_id=model.user_id, card_id=model.id)
        return _to_domain(model)

    async def get_card_by_id(self, card_id: int, user_id: int) -> SrsCard | None:
        result = await self._session.execute(
            select(SrsCardModel).where(
                SrsCardModel.id == card_id,
                SrsCardModel.user_id == user_id,
            ),
        )
        model = result.scalar_one_or_none()
        if model is None:
            return None

        return _to_domain(model)

    async def get_card_by_id_for_update(self, card_id: int, user_id: int) -> SrsCard | None:
        result = await self._session.execute(
            select(SrsCardModel)
            .where(
                SrsCardModel.id == card_id,
                SrsCardModel.user_id == user_id,
            )
            .with_for_update(),
        )
        model = result.scalar_one_or_none()
        if model is None:
            return None

        return _to_domain(model)

    async def create_review(self, review: Review) -> Review:
        model = SrsReviewModel(
            card_id=review.card_id,
            user_id=review.user_id,
            rating=review.rating.to_score(),
            reviewed_at=review.reviewed_at,
            response_time_ms=review.response_time_ms,
            session_length_s=review.session_length_s,
            parallel_mode_active=review.parallel_mode_active,
            session_id=review.session_id,
            previous_fsrs_state=review.previous_fsrs_state,
            previous_stability=review.previous_stability,
            previous_difficulty=review.previous_difficulty,
            previous_reps=review.previous_reps,
            previous_lapses=review.previous_lapses,
        )
        self._session.add(model)
        await self._session.commit()
        await self._session.refresh(model)

        logger.info(
            "srs_review_created",
            user_id=model.user_id,
            card_id=model.card_id,
            rating=model.rating,
        )
        return _review_to_domain(model)

    async def save_review_result(self, card: SrsCard, review: Review) -> tuple[SrsCard, Review]:
        if card.id is None:
            msg = "Card id is required for updates"
            raise CardNotFoundError(msg)

        result = await self._session.execute(
            select(SrsCardModel).where(
                SrsCardModel.id == card.id,
                SrsCardModel.user_id == card.user_id,
            ),
        )
        model = result.scalar_one_or_none()
        if model is None:
            msg = "Card not found"
            raise CardNotFoundError(msg)

        model.term_id = card.term_id
        model.language = card.language
        model.due_at = card.due_at
        model.fsrs_state = card.fsrs_state
        model.stability = card.stability
        model.difficulty = card.difficulty
        model.reps = card.reps
        model.lapses = card.lapses

        review_model = SrsReviewModel(
            card_id=review.card_id,
            user_id=review.user_id,
            rating=review.rating.to_score(),
            reviewed_at=review.reviewed_at,
            response_time_ms=review.response_time_ms,
            session_length_s=review.session_length_s,
            parallel_mode_active=review.parallel_mode_active,
            session_id=review.session_id,
            previous_fsrs_state=review.previous_fsrs_state,
            previous_stability=review.previous_stability,
            previous_difficulty=review.previous_difficulty,
            previous_reps=review.previous_reps,
            previous_lapses=review.previous_lapses,
        )
        self._session.add(review_model)
        await self._session.commit()
        await self._session.refresh(model)
        await self._session.refresh(review_model)

        logger.info(
            "srs_review_result_saved",
            user_id=model.user_id,
            card_id=model.id,
            rating=review_model.rating,
        )
        return _to_domain(model), _review_to_domain(review_model)

    async def get_last_review(self, card_id: int, user_id: int) -> Review | None:
        result = await self._session.execute(
            select(SrsReviewModel)
            .where(
                SrsReviewModel.card_id == card_id,
                SrsReviewModel.user_id == user_id,
            )
            .order_by(SrsReviewModel.reviewed_at.desc())
            .limit(1),
        )
        model = result.scalar_one_or_none()
        if model is None:
            return None

        return _review_to_domain(model)

    async def get_last_review_for_update(self, card_id: int, user_id: int) -> Review | None:
        result = await self._session.execute(
            select(SrsReviewModel)
            .where(
                SrsReviewModel.card_id == card_id,
                SrsReviewModel.user_id == user_id,
            )
            .order_by(SrsReviewModel.reviewed_at.desc())
            .limit(1)
            .with_for_update(),
        )
        model = result.scalar_one_or_none()
        if model is None:
            return None

        return _review_to_domain(model)

    async def delete_review(self, review_id: int) -> None:
        result = await self._session.execute(
            select(SrsReviewModel).where(SrsReviewModel.id == review_id),
        )
        model = result.scalar_one_or_none()
        if model is None:
            msg = "Review not found"
            raise NoReviewToUndoError(msg)

        await self._session.delete(model)

        logger.info(
            "srs_review_deleted",
            review_id=review_id,
        )

    async def update_card_with_delete_review(self, card: SrsCard, review_id: int) -> SrsCard:
        if card.id is None:
            msg = "Card id is required for updates"
            raise CardNotFoundError(msg)

        result = await self._session.execute(
            select(SrsCardModel)
            .where(
                SrsCardModel.id == card.id,
                SrsCardModel.user_id == card.user_id,
            )
            .with_for_update(),
        )
        card_model = result.scalar_one_or_none()
        if card_model is None:
            msg = "Card not found"
            raise CardNotFoundError(msg)

        card_model.term_id = card.term_id
        card_model.language = card.language
        card_model.due_at = card.due_at
        card_model.fsrs_state = card.fsrs_state
        card_model.stability = card.stability
        card_model.difficulty = card.difficulty
        card_model.reps = card.reps
        card_model.lapses = card.lapses

        review_result = await self._session.execute(
            select(SrsReviewModel).where(
                SrsReviewModel.id == review_id,
                SrsReviewModel.card_id == card.id,
                SrsReviewModel.user_id == card.user_id,
            ),
        )
        review_model = review_result.scalar_one_or_none()
        if review_model is None:
            msg = "Review not found for this card"
            raise NoReviewToUndoError(msg)
        await self._session.delete(review_model)

        await self._session.commit()
        await self._session.refresh(card_model)

        logger.info(
            "srs_card_updated_with_review_delete",
            user_id=card_model.user_id,
            card_id=card_model.id,
        )
        return _to_domain(card_model)

    async def rollback(self) -> None:
        await self._session.rollback()

    async def get_queue_stats(
        self, user_id: int, now: datetime, collection_id: int | None = None
    ) -> QueueStats:
        overdue_cutoff = now - timedelta(days=1)
        base_where = [
            SrsCardModel.user_id == user_id,
            SrsCardModel.due_at <= now,
        ]
        if collection_id is not None:
            base_where.append(CollectionTermModel.collection_id == collection_id)

        count_stmt = select(
            func.count(SrsCardModel.id),
            func.count(SrsCardModel.id).filter(SrsCardModel.due_at < overdue_cutoff),
        ).where(*base_where)
        if collection_id is not None:
            count_stmt = count_stmt.join(
                CollectionTermModel,
                SrsCardModel.term_id == CollectionTermModel.term_id,
            )

        counts_result = await self._session.execute(count_stmt)
        due_count, overdue_count = counts_result.one()

        avg_result = await self._session.execute(
            select(func.avg(SrsReviewModel.response_time_ms)).where(
                SrsReviewModel.user_id == user_id,
                SrsReviewModel.response_time_ms.is_not(None),
            ),
        )
        avg_response_time_ms = avg_result.scalar_one_or_none()
        due_count_value = int(due_count or 0)
        estimated_minutes = 0
        if due_count_value > 0 and avg_response_time_ms is not None:
            estimated_minutes = ceil(due_count_value * float(avg_response_time_ms) / 60000)

        logger.info("srs_queue_stats_loaded", user_id=user_id)
        return QueueStats(
            due_count=due_count_value,
            overdue_count=int(overdue_count or 0),
            estimated_minutes=estimated_minutes,
        )

    async def list_due_cards(
        self,
        user_id: int,
        now: datetime,
        mode: QueueMode,
        limit: int,
        offset: int,
        collection_id: int | None = None,
    ) -> DueCardsPage:
        queue_bucket = case((SrsCardModel.reps == 0, 1), else_=0)
        total_window = func.count(SrsCardModel.id).over().label("_total")
        base_where = [
            SrsCardModel.user_id == user_id,
            SrsCardModel.due_at <= now,
        ]
        if collection_id is not None:
            base_where.append(CollectionTermModel.collection_id == collection_id)

        stmt = (
            select(
                SrsCardModel,
                total_window,
                VocabularyTermModel.id.label("vt_id"),
                VocabularyTermModel.term.label("vt_term"),
                VocabularyTermModel.language.label("vt_language"),
                VocabularyTermModel.cefr_level.label("vt_cefr_level"),
                VocabularyTermModel.jlpt_level.label("vt_jlpt_level"),
                VocabularyTermModel.part_of_speech.label("vt_part_of_speech"),
            )
            .outerjoin(VocabularyTermModel, SrsCardModel.term_id == VocabularyTermModel.id)
            .where(*base_where)
        )
        if collection_id is not None:
            stmt = stmt.join(
                CollectionTermModel,
                SrsCardModel.term_id == CollectionTermModel.term_id,
            )

        stmt = (
            stmt.order_by(queue_bucket.asc(), SrsCardModel.due_at.asc(), SrsCardModel.id.asc())
            .offset(offset)
            .limit(limit)
        )

        result = await self._session.execute(stmt)
        rows = result.all()

        total_count = int(rows[0]._total) if rows else 0

        term_ids = [r.vt_id for r in rows if r.vt_id is not None]
        definitions_map: dict[int, list[dict[str, object]]] = {}
        if term_ids:
            def_result = await self._session.execute(
                select(VocabularyDefinitionModel).where(
                    VocabularyDefinitionModel.term_id.in_(term_ids)
                )
            )
            for d in def_result.scalars().all():
                definitions_map.setdefault(d.term_id, []).append(
                    {
                        "id": d.id,
                        "language": d.language,
                        "definition": d.definition,
                        "ipa": d.ipa,
                        "examples": d.examples,
                        "source": d.source,
                        "validated_against_jmdict": d.validated_against_jmdict,
                    }
                )

        items: list[DueCardWithTerm] = []
        for row in rows:
            card_model = row[0]
            card = _to_domain(card_model)
            embedded_term = None
            if row.vt_id is not None:
                embedded_term = EmbeddedTerm(
                    id=row.vt_id,
                    term=row.vt_term,
                    language=row.vt_language,
                    cefr_level=row.vt_cefr_level,
                    jlpt_level=row.vt_jlpt_level,
                    part_of_speech=row.vt_part_of_speech,
                    definitions=definitions_map.get(row.vt_id, []),
                )
            items.append(DueCardWithTerm(card=card, term=embedded_term))

        logger.info(
            "srs_due_cards_loaded",
            user_id=user_id,
            mode=mode.value,
            limit=limit,
            offset=offset,
        )
        return DueCardsPage(
            items=items,
            total_count=total_count,
            mode=mode,
            limit=limit,
            offset=offset,
        )

    async def get_session_reviews(self, user_id: int, session_id: UUID) -> list[SessionReviewRow]:
        stmt = (
            select(
                SrsReviewModel.card_id,
                SrsReviewModel.rating,
                SrsReviewModel.previous_stability,
                SrsCardModel.stability.label("current_stability"),
            )
            .join(SrsCardModel, SrsReviewModel.card_id == SrsCardModel.id)
            .where(
                SrsReviewModel.session_id == session_id,
                SrsReviewModel.user_id == user_id,
            )
            .order_by(SrsReviewModel.reviewed_at.asc())
        )
        result = await self._session.execute(stmt)
        rows = result.all()
        return [
            SessionReviewRow(
                card_id=row.card_id,
                rating=row.rating,
                previous_stability=row.previous_stability,
                current_card_stability=row.current_stability,
            )
            for row in rows
        ]

    async def find_term_ids_without_cards(
        self, user_id: int, collection_id: int, language: str
    ) -> list[int]:
        result = await self._session.execute(
            select(CollectionTermModel.term_id)
            .where(
                CollectionTermModel.collection_id == collection_id,
            )
            .where(
                ~exists(
                    select(SrsCardModel.id).where(
                        SrsCardModel.term_id == CollectionTermModel.term_id,
                        SrsCardModel.user_id == user_id,
                        SrsCardModel.language == language,
                    )
                )
            )
        )
        return [row[0] for row in result.all()]

    async def count_due_cards_for_date(self, user_id: int, date_end: datetime) -> int:
        result = await self._session.execute(
            select(func.count(SrsCardModel.id)).where(
                SrsCardModel.user_id == user_id,
                SrsCardModel.due_at <= date_end,
            )
        )
        return int(result.scalar_one() or 0)

    async def count_due_cards_by_buckets(
        self, user_id: int, today_end: datetime, tomorrow_end: datetime, week_end: datetime
    ) -> UpcomingSchedule:
        result = await self._session.execute(
            select(
                func.count(SrsCardModel.id).filter(SrsCardModel.due_at <= today_end),
                func.count(SrsCardModel.id).filter(
                    SrsCardModel.due_at > today_end,
                    SrsCardModel.due_at <= tomorrow_end,
                ),
                func.count(SrsCardModel.id).filter(
                    SrsCardModel.due_at > tomorrow_end,
                    SrsCardModel.due_at <= week_end,
                ),
            ).where(
                SrsCardModel.user_id == user_id,
                SrsCardModel.due_at <= week_end,
            )
        )
        today_count, tomorrow_count, this_week_count = result.one()

        avg_result = await self._session.execute(
            select(func.avg(SrsReviewModel.response_time_ms)).where(
                SrsReviewModel.user_id == user_id,
                SrsReviewModel.response_time_ms.is_not(None),
            ),
        )
        avg_response_time_ms = avg_result.scalar_one_or_none()

        def calc_minutes(count: int) -> int:
            if count == 0:
                return 0
            if avg_response_time_ms is not None:
                return ceil(count * float(avg_response_time_ms) / 60000)
            return ceil(count * 10 / 60)

        logger.info("srs_schedule_buckets_loaded", user_id=user_id)
        return UpcomingSchedule(
            today=ScheduleBucket(
                due_count=int(today_count), estimated_minutes=calc_minutes(int(today_count))
            ),
            tomorrow=ScheduleBucket(
                due_count=int(tomorrow_count), estimated_minutes=calc_minutes(int(tomorrow_count))
            ),
            this_week=ScheduleBucket(
                due_count=int(this_week_count),
                estimated_minutes=calc_minutes(int(this_week_count)),
            ),
        )
