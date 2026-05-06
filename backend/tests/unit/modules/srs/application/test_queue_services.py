from datetime import UTC, datetime, timedelta

from src.app.modules.srs.application.services import QueueStatsService
from src.app.modules.srs.domain.entities import DueCardsPage, QueueStats, SrsCard
from src.app.modules.srs.domain.interfaces import SrsCardRepository
from src.app.modules.srs.domain.value_objects import QueueMode


class InMemorySrsCardRepository(SrsCardRepository):
    def __init__(self, stats: QueueStats, cards: list[SrsCard] | None = None) -> None:
        self._stats = stats
        self._cards = cards or []

    async def get_queue_stats(self, user_id: int, now: datetime) -> QueueStats:
        _ = (user_id, now)
        return self._stats

    async def list_due_cards(
        self,
        user_id: int,
        now: datetime,
        mode: QueueMode,
        limit: int,
        offset: int,
    ) -> DueCardsPage:
        _ = (user_id, now)
        due_cards = sorted(self._cards, key=lambda card: (card.due_at, card.id or 0))
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
