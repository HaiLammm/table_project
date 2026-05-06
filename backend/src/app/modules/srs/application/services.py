from datetime import UTC, datetime, timedelta
from math import ceil
from uuid import UUID

import structlog
from fsrs import Card, Scheduler

from src.app.modules.srs.domain.entities import (
    DueCardsPage,
    QueueStats,
    Review,
    ReviewResult,
    SrsCard,
)
from src.app.modules.srs.domain.exceptions import CardNotDueError, CardNotFoundError
from src.app.modules.srs.domain.interfaces import SrsCardRepository
from src.app.modules.srs.domain.value_objects import FSRSState, QueueMode, Rating

logger = structlog.get_logger().bind(module="srs_service")


def _format_interval(interval: timedelta) -> str:
    total_seconds = max(int(interval.total_seconds()), 0)
    if total_seconds < 3600:
        return f"{max(1, ceil(total_seconds / 60))}m"
    if total_seconds < 86400:
        return f"{ceil(total_seconds / 3600)}h"

    return f"{ceil(total_seconds / 86400)}d"


class QueueStatsService:
    def __init__(self, srs_card_repository: SrsCardRepository) -> None:
        self._srs_card_repository = srs_card_repository

    async def get_queue_stats(self, user_id: int) -> QueueStats:
        queue_stats = await self._srs_card_repository.get_queue_stats(user_id, datetime.now(UTC))
        estimated_minutes = queue_stats.estimated_minutes
        if estimated_minutes == 0 and queue_stats.due_count > 0:
            estimated_minutes = ceil(queue_stats.due_count * 10 / 60)

        return QueueStats(
            due_count=queue_stats.due_count,
            overdue_count=queue_stats.overdue_count,
            estimated_minutes=estimated_minutes,
        )

    async def get_due_cards(
        self,
        user_id: int,
        mode: QueueMode,
        limit: int,
        offset: int,
    ) -> DueCardsPage:
        effective_limit = 30 if mode is QueueMode.CATCHUP else limit
        effective_offset = 0 if mode is QueueMode.CATCHUP else offset
        return await self._srs_card_repository.list_due_cards(
            user_id=user_id,
            now=datetime.now(UTC),
            mode=mode,
            limit=effective_limit,
            offset=effective_offset,
        )


class ReviewSchedulingService:
    def __init__(
        self,
        srs_card_repository: SrsCardRepository,
        scheduler: Scheduler | None = None,
    ) -> None:
        self._srs_card_repository = srs_card_repository
        self._scheduler = scheduler or Scheduler()

    async def create_card_for_term(self, user_id: int, term_id: int, language: str) -> SrsCard:
        fsrs_card = Card()
        card = SrsCard(
            user_id=user_id,
            term_id=term_id,
            language=language,
            due_at=fsrs_card.due,
            fsrs_state=FSRSState.from_card(fsrs_card),
            stability=fsrs_card.stability,
            difficulty=fsrs_card.difficulty,
            reps=0,
            lapses=0,
        )
        created_card = await self._srs_card_repository.create_card(card)
        logger.info(
            "srs_card_initialized",
            user_id=user_id,
            term_id=term_id,
            language=language,
        )
        return created_card

    async def review_card(
        self,
        card_id: int,
        user_id: int,
        rating: Rating,
        response_time_ms: int | None = None,
        session_id: UUID | None = None,
    ) -> ReviewResult:
        stored_card = await self._srs_card_repository.get_card_by_id_for_update(card_id, user_id)
        if stored_card is None:
            await self._srs_card_repository.rollback()
            msg = "Card not found"
            raise CardNotFoundError(msg, details={"card_id": card_id, "user_id": user_id})

        try:
            review_datetime = datetime.now(UTC)
            if stored_card.due_at > review_datetime:
                msg = "Card is not due yet"
                raise CardNotDueError(
                    msg,
                    details={
                        "card_id": card_id,
                        "user_id": user_id,
                        "due_at": stored_card.due_at.isoformat(),
                    },
                )

            fsrs_card = FSRSState.to_card(
                stored_card.fsrs_state, fallback_due_at=stored_card.due_at
            )
            updated_fsrs_card, review_log = self._scheduler.review_card(
                fsrs_card,
                rating.to_fsrs(),
                review_datetime=review_datetime,
                review_duration=response_time_ms,
            )
            updated_card = SrsCard(
                id=stored_card.id,
                user_id=stored_card.user_id,
                term_id=stored_card.term_id,
                language=stored_card.language,
                due_at=updated_fsrs_card.due,
                fsrs_state=FSRSState.from_card(updated_fsrs_card),
                stability=updated_fsrs_card.stability,
                difficulty=updated_fsrs_card.difficulty,
                reps=stored_card.reps + 1,
                lapses=stored_card.lapses + int(rating is Rating.AGAIN),
                created_at=stored_card.created_at,
                updated_at=stored_card.updated_at,
            )
            persisted_card, persisted_review = await self._srs_card_repository.save_review_result(
                updated_card,
                Review(
                    card_id=card_id,
                    user_id=user_id,
                    rating=rating,
                    reviewed_at=review_log.review_datetime,
                    response_time_ms=response_time_ms,
                    session_id=session_id,
                ),
            )
        except Exception:
            await self._srs_card_repository.rollback()
            raise

        logger.info(
            "srs_card_reviewed",
            user_id=user_id,
            card_id=card_id,
            rating=rating.value,
        )
        return ReviewResult(
            card=persisted_card,
            reviewed_at=persisted_review.reviewed_at,
            next_due_at=persisted_card.due_at,
            interval_display=_format_interval(persisted_card.due_at - review_log.review_datetime),
        )
