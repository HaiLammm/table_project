from datetime import UTC, datetime, timedelta

from src.app.modules.srs.application.services import QueueStatsService
from src.app.modules.srs.domain.entities import DueCardsPage, QueueStats, Review, SrsCard
from src.app.modules.srs.domain.exceptions import DuplicateCardError
from src.app.modules.srs.domain.interfaces import SrsCardRepository
from src.app.modules.srs.domain.value_objects import QueueMode


class InMemorySrsCardRepository(SrsCardRepository):
    def __init__(self, stats: QueueStats, cards: list[SrsCard] | None = None) -> None:
        self._stats = stats
        self._cards = cards or []
        self.rollback_called = False

    async def get_queue_stats(self, user_id: int, now: datetime) -> QueueStats:
        _ = (user_id, now)
        return self._stats

    async def create_card(self, card: SrsCard) -> SrsCard:
        if any(
            existing.user_id == card.user_id
            and existing.term_id == card.term_id
            and existing.language == card.language
            for existing in self._cards
        ):
            msg = "Card already exists for this term and language"
            raise DuplicateCardError(msg)

        card.id = len(self._cards) + 1
        self._cards.append(card)
        return card

    async def update_card(self, card: SrsCard) -> SrsCard:
        for index, existing in enumerate(self._cards):
            if existing.id == card.id:
                self._cards[index] = card
                return card

        msg = "Card not found"
        raise AssertionError(msg)

    async def get_card_by_id(self, card_id: int, user_id: int) -> SrsCard | None:
        for card in self._cards:
            if card.id == card_id and card.user_id == user_id:
                return card

        return None

    async def get_card_by_id_for_update(self, card_id: int, user_id: int) -> SrsCard | None:
        return await self.get_card_by_id(card_id, user_id)

    async def create_review(self, review: Review) -> Review:
        _ = review
        return review

    async def save_review_result(self, card: SrsCard, review: Review) -> tuple[SrsCard, Review]:
        return await self.update_card(card), review

    async def rollback(self) -> None:
        self.rollback_called = True

    async def list_due_cards(
        self,
        user_id: int,
        now: datetime,
        mode: QueueMode,
        limit: int,
        offset: int,
    ) -> DueCardsPage:
        _ = (user_id, now)
        due_cards = sorted(
            self._cards,
            key=lambda card: (int(card.reps == 0), card.due_at, card.id or 0),
        )
        return DueCardsPage(
            items=due_cards[offset : offset + limit],
            total_count=len(due_cards),
            mode=mode,
            limit=limit,
            offset=offset,
        )


async def test_queue_stats_service_returns_zero_card_queue() -> None:
    service = QueueStatsService(
        InMemorySrsCardRepository(QueueStats(due_count=0, overdue_count=0, estimated_minutes=0)),
    )

    queue_stats = await service.get_queue_stats(7)

    assert queue_stats.due_count == 0
    assert queue_stats.overdue_count == 0
    assert queue_stats.estimated_minutes == 0
    assert queue_stats.has_overdue is False


async def test_queue_stats_service_calculates_neutral_estimate_for_normal_queue() -> None:
    service = QueueStatsService(
        InMemorySrsCardRepository(QueueStats(due_count=6, overdue_count=2, estimated_minutes=0)),
    )

    queue_stats = await service.get_queue_stats(7)

    assert queue_stats.due_count == 6
    assert queue_stats.overdue_count == 2
    assert queue_stats.estimated_minutes == 1
    assert queue_stats.has_overdue is True


async def test_queue_stats_service_handles_extended_absence_counts() -> None:
    service = QueueStatsService(
        InMemorySrsCardRepository(
            QueueStats(due_count=132, overdue_count=104, estimated_minutes=0)
        ),
    )

    queue_stats = await service.get_queue_stats(7)

    assert queue_stats.due_count == 132
    assert queue_stats.overdue_count == 104
    assert queue_stats.estimated_minutes == 22
    assert queue_stats.has_overdue is True


async def test_queue_stats_service_returns_exactly_thirty_cards_for_catchup_mode() -> None:
    now = datetime.now(UTC)
    cards = [
        SrsCard(
            id=index + 1,
            user_id=7,
            term_id=None,
            language="en",
            due_at=now - timedelta(days=120 - index),
            fsrs_state={},
        )
        for index in range(45)
    ]
    service = QueueStatsService(
        InMemorySrsCardRepository(
            QueueStats(due_count=45, overdue_count=45, estimated_minutes=0),
            cards=cards,
        ),
    )

    catchup_queue = await service.get_due_cards(7, QueueMode.CATCHUP, limit=100, offset=10)

    assert catchup_queue.mode is QueueMode.CATCHUP
    assert catchup_queue.limit == 30
    assert catchup_queue.offset == 0
    assert len(catchup_queue.items) == 30
    assert catchup_queue.items[0] == cards[0]
    assert catchup_queue.items[-1] == cards[29]


async def test_queue_stats_service_preserves_pagination_for_full_mode() -> None:
    now = datetime.now(UTC)
    cards = [
        SrsCard(
            id=index + 1,
            user_id=7,
            term_id=None,
            language="en",
            due_at=now.replace(minute=0, second=0, microsecond=0) - timedelta(hours=index),
            fsrs_state={},
        )
        for index in range(6)
    ]
    service = QueueStatsService(
        InMemorySrsCardRepository(
            QueueStats(due_count=6, overdue_count=6, estimated_minutes=0),
            cards=cards,
        ),
    )

    full_queue = await service.get_due_cards(7, QueueMode.FULL, limit=2, offset=1)

    assert full_queue.mode is QueueMode.FULL
    assert full_queue.limit == 2
    assert full_queue.offset == 1
    assert [card.id for card in full_queue.items] == [5, 4]


async def test_queue_stats_service_preserves_repository_estimate_when_review_data_exists() -> None:
    service = QueueStatsService(
        InMemorySrsCardRepository(QueueStats(due_count=12, overdue_count=3, estimated_minutes=4)),
    )

    queue_stats = await service.get_queue_stats(7)

    assert queue_stats.due_count == 12
    assert queue_stats.overdue_count == 3
    assert queue_stats.estimated_minutes == 4


async def test_queue_stats_service_keeps_overdue_due_then_new_ordering() -> None:
    now = datetime.now(UTC)
    cards = [
        SrsCard(
            id=1,
            user_id=7,
            term_id=101,
            language="en",
            due_at=now - timedelta(days=4),
            fsrs_state={},
        ),
        SrsCard(
            id=2,
            user_id=7,
            term_id=102,
            language="en",
            due_at=now - timedelta(hours=2),
            fsrs_state={},
        ),
        SrsCard(
            id=3,
            user_id=7,
            term_id=103,
            language="en",
            due_at=now - timedelta(seconds=1),
            fsrs_state={},
        ),
    ]
    service = QueueStatsService(
        InMemorySrsCardRepository(
            QueueStats(due_count=3, overdue_count=1, estimated_minutes=1),
            cards=cards,
        ),
    )

    queue = await service.get_due_cards(7, QueueMode.FULL, limit=10, offset=0)

    assert [card.term_id for card in queue.items] == [101, 102, 103]


async def test_queue_stats_service_pushes_stale_new_cards_after_reviewed_due_cards() -> None:
    now = datetime.now(UTC)
    cards = [
        SrsCard(
            id=1,
            user_id=7,
            term_id=101,
            language="en",
            due_at=now - timedelta(days=10),
            fsrs_state={},
            reps=0,
        ),
        SrsCard(
            id=2,
            user_id=7,
            term_id=102,
            language="en",
            due_at=now - timedelta(hours=1),
            fsrs_state={},
            reps=3,
        ),
    ]
    repository = InMemorySrsCardRepository(
        QueueStats(due_count=2, overdue_count=1, estimated_minutes=1),
        cards=cards,
    )

    queue = await repository.list_due_cards(7, now, QueueMode.FULL, limit=10, offset=0)

    assert [card.term_id for card in queue.items] == [102, 101]
