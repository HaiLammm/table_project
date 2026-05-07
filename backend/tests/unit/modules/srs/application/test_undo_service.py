from datetime import UTC, datetime
from uuid import UUID

import pytest

from src.app.modules.srs.application.services import ReviewSchedulingService
from src.app.modules.srs.domain.entities import (
    DueCardsPage,
    QueueStats,
    Review,
    ReviewResult,
    SessionReviewRow,
    SrsCard,
)
from src.app.modules.srs.domain.exceptions import NoReviewToUndoError
from src.app.modules.srs.domain.interfaces import SrsCardRepository
from src.app.modules.srs.domain.value_objects import QueueMode, Rating


class InMemoryUndoRepository(SrsCardRepository):
    def __init__(self) -> None:
        self._cards: dict[int, SrsCard] = {}
        self._reviews: dict[int, Review] = {}
        self._next_card_id = 1
        self._next_review_id = 1
        self.rollback_called = False

    async def get_queue_stats(self, user_id: int, now: datetime) -> QueueStats:
        return QueueStats(due_count=0, overdue_count=0, estimated_minutes=0)

    async def list_due_cards(
        self,
        user_id: int,
        now: datetime,
        mode: QueueMode,
        limit: int,
        offset: int,
    ) -> DueCardsPage:
        return DueCardsPage(items=[], total_count=0, mode=mode, limit=limit, offset=offset)

    async def create_card(self, card: SrsCard) -> SrsCard:
        card.id = self._next_card_id
        self._next_card_id += 1
        self._cards[card.id] = card
        return card

    async def update_card(self, card: SrsCard) -> SrsCard:
        assert card.id is not None
        self._cards[card.id] = card
        return card

    async def get_card_by_id(self, card_id: int, user_id: int) -> SrsCard | None:
        card = self._cards.get(card_id)
        if card is None or card.user_id != user_id:
            return None
        return card

    async def get_card_by_id_for_update(self, card_id: int, user_id: int) -> SrsCard | None:
        return await self.get_card_by_id(card_id, user_id)

    async def create_review(self, review: Review) -> Review:
        review.id = self._next_review_id
        self._next_review_id += 1
        self._reviews[review.id] = review
        return review

    async def save_review_result(self, card: SrsCard, review: Review) -> tuple[SrsCard, Review]:
        updated_card = await self.update_card(card)
        saved_review = await self.create_review(review)
        return updated_card, saved_review

    async def get_last_review(self, card_id: int, user_id: int) -> Review | None:
        reviews = sorted(
            [r for r in self._reviews.values() if r.card_id == card_id and r.user_id == user_id],
            key=lambda r: r.reviewed_at or datetime.min.replace(tzinfo=UTC),
            reverse=True,
        )
        return reviews[0] if reviews else None

    async def delete_review(self, review_id: int) -> None:
        self._reviews.pop(review_id, None)

    async def rollback(self) -> None:
        self.rollback_called = True

    async def get_last_review_for_update(self, card_id: int, user_id: int) -> Review | None:
        return await self.get_last_review(card_id, user_id)

    async def update_card_with_delete_review(self, card: SrsCard, review_id: int) -> SrsCard:
        await self.delete_review(review_id)
        return await self.update_card(card)

    async def get_session_reviews(self, user_id: int, session_id: UUID) -> list[SessionReviewRow]:
        return []

    async def count_due_cards_for_date(self, user_id: int, date_end: datetime) -> int:
        return 0


async def test_undo_last_review_restores_card_state() -> None:
    repository = InMemoryUndoRepository()
    service = ReviewSchedulingService(repository)
    created = await service.create_card_for_term(user_id=7, term_id=101, language="en")

    original_stability = created.stability
    original_difficulty = created.difficulty
    original_reps = created.reps
    original_lapses = created.lapses
    original_fsrs_state = created.fsrs_state
    original_due_at = created.due_at

    await service.review_card(
        card_id=created.id or 0,
        user_id=7,
        rating=Rating.GOOD,
        response_time_ms=1800,
    )

    undo_result = await service.undo_last_review(card_id=created.id or 0, user_id=7)

    assert isinstance(undo_result, ReviewResult)
    assert undo_result.card.id == created.id
    assert undo_result.card.stability == original_stability
    assert undo_result.card.difficulty == original_difficulty
    assert undo_result.card.reps == original_reps
    assert undo_result.card.lapses == original_lapses
    assert undo_result.card.fsrs_state == original_fsrs_state
    assert undo_result.card.due_at == original_due_at
    assert len(repository._reviews) == 0


async def test_undo_last_review_raises_when_no_review_exists() -> None:
    repository = InMemoryUndoRepository()
    service = ReviewSchedulingService(repository)
    created = await service.create_card_for_term(user_id=7, term_id=101, language="en")

    with pytest.raises(NoReviewToUndoError, match="No review to undo"):
        await service.undo_last_review(card_id=created.id or 0, user_id=7)


async def test_undo_last_review_raises_when_card_not_found() -> None:
    repository = InMemoryUndoRepository()
    service = ReviewSchedulingService(repository)
    created = await service.create_card_for_term(user_id=7, term_id=101, language="en")

    previous_state = {
        "fsrs_state": created.fsrs_state,
        "stability": created.stability,
        "difficulty": created.difficulty,
        "reps": created.reps,
        "lapses": created.lapses,
    }
    review = Review(
        card_id=created.id or 0,
        user_id=7,
        rating=Rating.GOOD,
        reviewed_at=datetime.now(UTC),
        previous_fsrs_state=previous_state["fsrs_state"],
        previous_stability=previous_state["stability"],
        previous_difficulty=previous_state["difficulty"],
        previous_reps=previous_state["reps"],
        previous_lapses=previous_state["lapses"],
    )
    await repository.create_review(review)
    del repository._cards[created.id or 0]

    from src.app.modules.srs.domain.exceptions import CardNotFoundError

    with pytest.raises(CardNotFoundError):
        await service.undo_last_review(card_id=created.id or 0, user_id=7)

    assert repository.rollback_called is True


async def test_undo_last_review_after_again_rating_restores_lapses() -> None:
    repository = InMemoryUndoRepository()
    service = ReviewSchedulingService(repository)
    created = await service.create_card_for_term(user_id=7, term_id=101, language="en")

    original_reps = created.reps
    original_lapses = created.lapses

    await service.review_card(
        card_id=created.id or 0,
        user_id=7,
        rating=Rating.AGAIN,
        response_time_ms=2500,
    )

    undo_result = await service.undo_last_review(card_id=created.id or 0, user_id=7)

    assert undo_result.card.reps == original_reps
    assert undo_result.card.lapses == original_lapses


async def test_undo_last_review_deletes_the_review_record() -> None:
    repository = InMemoryUndoRepository()
    service = ReviewSchedulingService(repository)
    created = await service.create_card_for_term(user_id=7, term_id=101, language="en")

    await service.review_card(
        card_id=created.id or 0,
        user_id=7,
        rating=Rating.GOOD,
        response_time_ms=1500,
    )

    assert len(repository._reviews) == 1
    await service.undo_last_review(card_id=created.id or 0, user_id=7)
    assert len(repository._reviews) == 0
