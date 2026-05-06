from datetime import datetime, timedelta
from math import ceil

import structlog
from sqlalchemy import case, func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from src.app.modules.srs.domain.entities import DueCardsPage, QueueStats, Review, SrsCard
from src.app.modules.srs.domain.exceptions import CardNotFoundError, DuplicateCardError
from src.app.modules.srs.domain.interfaces import SrsCardRepository
from src.app.modules.srs.domain.value_objects import QueueMode
from src.app.modules.srs.infrastructure.models import SrsCardModel, SrsReviewModel

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
            session_id=review.session_id,
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
        return Review(
            id=model.id,
            card_id=model.card_id,
            user_id=model.user_id,
            rating=review.rating,
            reviewed_at=model.reviewed_at,
            response_time_ms=model.response_time_ms,
            session_id=model.session_id,
        )

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
            session_id=review.session_id,
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
        return _to_domain(model), Review(
            id=review_model.id,
            card_id=review_model.card_id,
            user_id=review_model.user_id,
            rating=review.rating,
            reviewed_at=review_model.reviewed_at,
            response_time_ms=review_model.response_time_ms,
            session_id=review_model.session_id,
        )

    async def rollback(self) -> None:
        await self._session.rollback()

    async def get_queue_stats(self, user_id: int, now: datetime) -> QueueStats:
        overdue_cutoff = now - timedelta(days=1)
        counts_result = await self._session.execute(
            select(
                func.count(SrsCardModel.id),
                func.count(SrsCardModel.id).filter(SrsCardModel.due_at < overdue_cutoff),
            ).where(
                SrsCardModel.user_id == user_id,
                SrsCardModel.due_at <= now,
            ),
        )
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
    ) -> DueCardsPage:
        queue_bucket = case((SrsCardModel.reps == 0, 1), else_=0)
        total_result = await self._session.execute(
            select(func.count(SrsCardModel.id)).where(
                SrsCardModel.user_id == user_id,
                SrsCardModel.due_at <= now,
            ),
        )
        total_count = int(total_result.scalar_one() or 0)

        result = await self._session.execute(
            select(SrsCardModel)
            .where(
                SrsCardModel.user_id == user_id,
                SrsCardModel.due_at <= now,
            )
            .order_by(queue_bucket.asc(), SrsCardModel.due_at.asc(), SrsCardModel.id.asc())
            .offset(offset)
            .limit(limit),
        )

        logger.info(
            "srs_due_cards_loaded",
            user_id=user_id,
            mode=mode.value,
            limit=limit,
            offset=offset,
        )
        return DueCardsPage(
            items=[_to_domain(model) for model in result.scalars().all()],
            total_count=total_count,
            mode=mode,
            limit=limit,
            offset=offset,
        )
