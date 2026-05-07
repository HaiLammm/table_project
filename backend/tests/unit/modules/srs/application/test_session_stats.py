from datetime import datetime
from uuid import uuid4

from src.app.modules.srs.application.services import (
    MASTERY_STABILITY_THRESHOLD,
    ReviewSchedulingService,
)
from src.app.modules.srs.domain.entities import (
    DueCardsPage,
    QueueStats,
    Review,
    SessionReviewRow,
    SrsCard,
)
from src.app.modules.srs.domain.exceptions import DuplicateCardError
from src.app.modules.srs.domain.interfaces import SrsCardRepository
from src.app.modules.srs.domain.value_objects import QueueMode


class InMemorySessionStatsRepository(SrsCardRepository):
    def __init__(self) -> None:
        self._cards: dict[int, SrsCard] = {}
        self.reviews: list[Review] = []
        self._session_reviews: list[SessionReviewRow] = []
        self._due_count_for_date: int = 0
        self._next_card_id = 1
        self._next_review_id = 1
        self.rollback_called = False

    def set_session_reviews(self, reviews: list[SessionReviewRow]) -> None:
        self._session_reviews = reviews

    def set_due_count_for_date(self, count: int) -> None:
        self._due_count_for_date = count

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
        self.reviews.append(review)
        return review

    async def save_review_result(self, card: SrsCard, review: Review) -> tuple[SrsCard, Review]:
        updated_card = await self.update_card(card)
        saved_review = await self.create_review(review)
        return updated_card, saved_review

    async def get_last_review(self, card_id: int, user_id: int) -> Review | None:
        return None

    async def get_last_review_for_update(self, card_id: int, user_id: int) -> Review | None:
        return None

    async def delete_review(self, review_id: int) -> None:
        pass

    async def update_card_with_delete_review(self, card: SrsCard, review_id: int) -> SrsCard:
        return card

    async def rollback(self) -> None:
        self.rollback_called = True

    async def get_queue_stats(
        self, user_id: int, now: datetime, collection_id: int | None = None
    ) -> QueueStats:
        return QueueStats(due_count=0, overdue_count=0, estimated_minutes=0)

    async def list_due_cards(
        self,
        user_id: int,
        now: datetime,
        mode: QueueMode,
        limit: int,
        offset: int,
        collection_id: int | None = None,
    ) -> DueCardsPage:
        return DueCardsPage(items=[], total_count=0, mode=mode, limit=limit, offset=offset)

    async def get_session_reviews(
        self, user_id: int, session_id: object
    ) -> list[SessionReviewRow]:
        return self._session_reviews

    async def count_due_cards_for_date(self, user_id: int, date_end: datetime) -> int:
        return self._due_count_for_date

    async def find_term_ids_without_cards(
        self, user_id: int, collection_id: int, language: str
    ) -> list[int]:
        return []

    async def count_due_cards_by_buckets(
        self, user_id: int, today_end: datetime, tomorrow_end: datetime, week_end: datetime
    ):
        from src.app.modules.srs.domain.entities import ScheduleBucket, UpcomingSchedule

        return UpcomingSchedule(
            today=ScheduleBucket(due_count=0, estimated_minutes=0),
            tomorrow=ScheduleBucket(due_count=0, estimated_minutes=0),
            this_week=ScheduleBucket(due_count=0, estimated_minutes=0),
        )


async def test_empty_session_returns_zeros() -> None:
    repository = InMemorySessionStatsRepository()
    repository.set_session_reviews([])
    repository.set_due_count_for_date(0)
    service = ReviewSchedulingService(repository)

    stats = await service.get_session_stats(user_id=1, session_id=uuid4())

    assert stats.cards_reviewed == 0
    assert stats.cards_graduated == 0
    assert stats.cards_lapsed == 0
    assert stats.lapsed_card_ids == []
    assert stats.tomorrow_due_count == 0
    assert stats.tomorrow_estimated_minutes == 0


async def test_graduation_threshold_crossing() -> None:
    repository = InMemorySessionStatsRepository()
    repository.set_session_reviews(
        [
            SessionReviewRow(
                card_id=10,
                rating=3,
                previous_stability=5.0,
                current_card_stability=22.0,
            ),
        ]
    )
    repository.set_due_count_for_date(5)
    service = ReviewSchedulingService(repository)

    stats = await service.get_session_stats(user_id=1, session_id=uuid4())

    assert stats.cards_graduated == 1
    assert stats.tomorrow_due_count == 5
    assert stats.tomorrow_estimated_minutes == 1


async def test_card_already_above_threshold_not_graduated() -> None:
    repository = InMemorySessionStatsRepository()
    repository.set_session_reviews(
        [
            SessionReviewRow(
                card_id=10,
                rating=3,
                previous_stability=25.0,
                current_card_stability=30.0,
            ),
        ]
    )
    repository.set_due_count_for_date(3)
    service = ReviewSchedulingService(repository)

    stats = await service.get_session_stats(user_id=1, session_id=uuid4())

    assert stats.cards_graduated == 0


async def test_boundary_stability_exactly_21_counts_graduated() -> None:
    repository = InMemorySessionStatsRepository()
    repository.set_session_reviews(
        [
            SessionReviewRow(
                card_id=10,
                rating=3,
                previous_stability=5.0,
                current_card_stability=21.0,
            ),
        ]
    )
    repository.set_due_count_for_date(0)
    service = ReviewSchedulingService(repository)

    stats = await service.get_session_stats(user_id=1, session_id=uuid4())

    assert stats.cards_graduated == 1


async def test_lapsed_extraction_rating_again() -> None:
    repository = InMemorySessionStatsRepository()
    repository.set_session_reviews(
        [
            SessionReviewRow(
                card_id=1, rating=1, previous_stability=5.0, current_card_stability=2.0
            ),
            SessionReviewRow(
                card_id=2, rating=3, previous_stability=10.0, current_card_stability=15.0
            ),
            SessionReviewRow(
                card_id=1, rating=3, previous_stability=2.0, current_card_stability=8.0
            ),
        ]
    )
    repository.set_due_count_for_date(0)
    service = ReviewSchedulingService(repository)

    stats = await service.get_session_stats(user_id=1, session_id=uuid4())

    assert stats.cards_lapsed == 1
    assert stats.lapsed_card_ids == [1]


async def test_tomorrow_estimate_zero_cards() -> None:
    repository = InMemorySessionStatsRepository()
    repository.set_session_reviews(
        [
            SessionReviewRow(
                card_id=1, rating=3, previous_stability=5.0, current_card_stability=10.0
            ),
        ]
    )
    repository.set_due_count_for_date(0)
    service = ReviewSchedulingService(repository)

    stats = await service.get_session_stats(user_id=1, session_id=uuid4())

    assert stats.tomorrow_due_count == 0
    assert stats.tomorrow_estimated_minutes == 0


async def test_tomorrow_estimate_non_zero_cards() -> None:
    repository = InMemorySessionStatsRepository()
    repository.set_session_reviews(
        [
            SessionReviewRow(
                card_id=1, rating=3, previous_stability=5.0, current_card_stability=10.0
            ),
        ]
    )
    repository.set_due_count_for_date(18)
    service = ReviewSchedulingService(repository)

    stats = await service.get_session_stats(user_id=1, session_id=uuid4())

    assert stats.tomorrow_due_count == 18
    assert stats.tomorrow_estimated_minutes == 3


async def test_lapsed_deduplication_preserves_order() -> None:
    repository = InMemorySessionStatsRepository()
    repository.set_session_reviews(
        [
            SessionReviewRow(
                card_id=5, rating=1, previous_stability=3.0, current_card_stability=1.0
            ),
            SessionReviewRow(
                card_id=3, rating=1, previous_stability=4.0, current_card_stability=2.0
            ),
            SessionReviewRow(
                card_id=5, rating=1, previous_stability=1.0, current_card_stability=0.5
            ),
        ]
    )
    repository.set_due_count_for_date(0)
    service = ReviewSchedulingService(repository)

    stats = await service.get_session_stats(user_id=1, session_id=uuid4())

    assert stats.lapsed_card_ids == [5, 3]
    assert stats.cards_lapsed == 2


async def test_cards_reviewed_count() -> None:
    repository = InMemorySessionStatsRepository()
    repository.set_session_reviews(
        [
            SessionReviewRow(
                card_id=1, rating=3, previous_stability=5.0, current_card_stability=10.0
            ),
            SessionReviewRow(
                card_id=2, rating=4, previous_stability=8.0, current_card_stability=20.0
            ),
            SessionReviewRow(
                card_id=3, rating=1, previous_stability=2.0, current_card_stability=1.0
            ),
        ]
    )
    repository.set_due_count_for_date(0)
    service = ReviewSchedulingService(repository)

    stats = await service.get_session_stats(user_id=1, session_id=uuid4())

    assert stats.cards_reviewed == 3


async def test_none_previous_stability_not_graduated() -> None:
    repository = InMemorySessionStatsRepository()
    repository.set_session_reviews(
        [
            SessionReviewRow(
                card_id=10,
                rating=3,
                previous_stability=None,
                current_card_stability=22.0,
            ),
        ]
    )
    repository.set_due_count_for_date(0)
    service = ReviewSchedulingService(repository)

    stats = await service.get_session_stats(user_id=1, session_id=uuid4())

    assert stats.cards_graduated == 0


async def test_none_current_stability_not_graduated() -> None:
    repository = InMemorySessionStatsRepository()
    repository.set_session_reviews(
        [
            SessionReviewRow(
                card_id=10,
                rating=3,
                previous_stability=5.0,
                current_card_stability=None,
            ),
        ]
    )
    repository.set_due_count_for_date(0)
    service = ReviewSchedulingService(repository)

    stats = await service.get_session_stats(user_id=1, session_id=uuid4())

    assert stats.cards_graduated == 0


async def test_mastery_threshold_value() -> None:
    assert MASTERY_STABILITY_THRESHOLD == 21.0


async def test_multiple_graduations_in_single_session() -> None:
    repository = InMemorySessionStatsRepository()
    repository.set_session_reviews(
        [
            SessionReviewRow(
                card_id=1, rating=3, previous_stability=5.0, current_card_stability=22.0
            ),
            SessionReviewRow(
                card_id=2, rating=4, previous_stability=10.0, current_card_stability=30.0
            ),
            SessionReviewRow(
                card_id=3, rating=3, previous_stability=8.0, current_card_stability=15.0
            ),
        ]
    )
    repository.set_due_count_for_date(12)
    service = ReviewSchedulingService(repository)

    stats = await service.get_session_stats(user_id=1, session_id=uuid4())

    assert stats.cards_graduated == 2
    assert stats.cards_lapsed == 0
    assert stats.tomorrow_estimated_minutes == 2
