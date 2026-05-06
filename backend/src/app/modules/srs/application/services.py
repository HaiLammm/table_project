from datetime import UTC, datetime
from math import ceil

from src.app.modules.srs.domain.entities import DueCardsPage, QueueStats
from src.app.modules.srs.domain.interfaces import SrsCardRepository
from src.app.modules.srs.domain.value_objects import QueueMode


class QueueStatsService:
    def __init__(self, srs_card_repository: SrsCardRepository) -> None:
        self._srs_card_repository = srs_card_repository

    async def get_queue_stats(self, user_id: int) -> QueueStats:
        queue_stats = await self._srs_card_repository.get_queue_stats(user_id, datetime.now(UTC))
        return QueueStats(
            due_count=queue_stats.due_count,
            overdue_count=queue_stats.overdue_count,
            estimated_minutes=ceil(queue_stats.due_count * 10 / 60),
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
