from datetime import datetime
from uuid import uuid4

import pytest

from src.app.modules.srs.application.services import ReviewSchedulingService
from src.app.modules.srs.domain.entities import (
    DueCardsPage,
    QueueStats,
    Review,
    ReviewResult,
    SrsCard,
)
from src.app.modules.srs.domain.exceptions import DuplicateCardError
from src.app.modules.srs.domain.interfaces import SrsCardRepository
from src.app.modules.srs.domain.value_objects import QueueMode, Rating


class InMemoryReviewRepository(SrsCardRepository):
    def __init__(self) -> None:
        self._cards: dict[int, SrsCard] = {}
        self.reviews: list[Review] = []
        self._next_card_id = 1
        self._next_review_id = 1
        self.rollback_called = False

    async def get_queue_stats(self, user_id: int, now: datetime) -> QueueStats:
        due_cards = [
            card for card in self._cards.values() if card.user_id == user_id and card.due_at <= now
        ]
        return QueueStats(
            due_count=len(due_cards),
            overdue_count=0,
            estimated_minutes=0,
        )

    async def list_due_cards(
        self,
        user_id: int,
        now: datetime,
        mode: QueueMode,
        limit: int,
        offset: int,
    ) -> DueCardsPage:
        items = sorted(
            [
                card
                for card in self._cards.values()
                if card.user_id == user_id and card.due_at <= now
            ],
            key=lambda card: (card.due_at, card.id or 0),
        )
        return DueCardsPage(
            items=items[offset : offset + limit],
            total_count=len(items),
            mode=mode,
            limit=limit,
            offset=offset,
        )

    async def create_card(self, card: SrsCard) -> SrsCard:
        if any(
            existing.user_id == card.user_id
            and existing.term_id == card.term_id
            and existing.language == card.language
            for existing in self._cards.values()
        ):
            msg = "Card already exists for this term and language"
            raise DuplicateCardError(msg)

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
        self.reviews.append(review)
        return review

    async def save_review_result(self, card: SrsCard, review: Review) -> tuple[SrsCard, Review]:
        updated_card = await self.update_card(card)
        saved_review = await self.create_review(review)
        return updated_card, saved_review

    async def rollback(self) -> None:
        self.rollback_called = True


async def test_review_scheduling_service_initializes_fsrs_card_defaults() -> None:
    repository = InMemoryReviewRepository()
    service = ReviewSchedulingService(repository)

    created = await service.create_card_for_term(user_id=7, term_id=101, language="en")

    assert created.id == 1
    assert created.term_id == 101
    assert created.language == "en"
    assert created.stability is None
    assert created.difficulty is None
    assert created.reps == 0
    assert created.lapses == 0
    assert created.fsrs_state["state"] == 1
    assert created.fsrs_state["step"] == 0
    assert datetime.fromisoformat(str(created.fsrs_state["due"])) == created.due_at


@pytest.mark.parametrize(
    ("rating", "expected_lapses"),
    [
        (Rating.AGAIN, 1),
        (Rating.HARD, 0),
        (Rating.GOOD, 0),
        (Rating.EASY, 0),
    ],
)
async def test_review_scheduling_service_transitions_fsrs_state_for_each_rating(
    rating: Rating,
    expected_lapses: int,
) -> None:
    repository = InMemoryReviewRepository()
    service = ReviewSchedulingService(repository)
    created = await service.create_card_for_term(user_id=7, term_id=101, language="en")

    review_result = await service.review_card(
        card_id=created.id or 0,
        user_id=7,
        rating=rating,
        response_time_ms=1800,
        session_id=uuid4(),
    )

    assert isinstance(review_result, ReviewResult)
    assert review_result.card.id == created.id
    assert review_result.card.due_at > created.due_at
    assert review_result.card.stability is not None
    assert review_result.card.difficulty is not None
    assert review_result.card.reps == 1
    assert review_result.card.lapses == expected_lapses
    assert review_result.next_due_at == review_result.card.due_at
    assert review_result.interval_display
    assert len(repository.reviews) == 1
    assert repository.reviews[0].rating is rating
    assert repository.reviews[0].response_time_ms == 1800


async def test_review_scheduling_service_creates_independent_cards_per_language() -> None:
    repository = InMemoryReviewRepository()
    service = ReviewSchedulingService(repository)

    english_card = await service.create_card_for_term(user_id=7, term_id=501, language="en")
    japanese_card = await service.create_card_for_term(user_id=7, term_id=501, language="jp")

    assert english_card.id != japanese_card.id
    assert english_card.term_id == japanese_card.term_id == 501
    assert english_card.language == "en"
    assert japanese_card.language == "jp"


async def test_review_scheduling_service_rolls_back_when_review_persistence_fails() -> None:
    class FailingReviewRepository(InMemoryReviewRepository):
        async def save_review_result(
            self,
            card: SrsCard,
            review: Review,
        ) -> tuple[SrsCard, Review]:
            _ = (card, review)
            raise RuntimeError("persist failed")

    repository = FailingReviewRepository()
    service = ReviewSchedulingService(repository)
    created = await service.create_card_for_term(user_id=7, term_id=101, language="en")

    with pytest.raises(RuntimeError, match="persist failed"):
        await service.review_card(
            card_id=created.id or 0,
            user_id=7,
            rating=Rating.GOOD,
        )

    assert repository.rollback_called is True
