from abc import ABC, abstractmethod
from datetime import datetime

from src.app.modules.srs.domain.entities import DueCardsPage, QueueStats
from src.app.modules.srs.domain.value_objects import QueueMode


class SrsCardRepository(ABC):
    @abstractmethod
    async def get_queue_stats(self, user_id: int, now: datetime) -> QueueStats:
        raise NotImplementedError

    @abstractmethod
    async def list_due_cards(
        self,
        user_id: int,
        now: datetime,
        mode: QueueMode,
        limit: int,
        offset: int,
    ) -> DueCardsPage:
        raise NotImplementedError
