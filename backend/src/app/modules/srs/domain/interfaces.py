from abc import ABC, abstractmethod
from datetime import datetime

from src.app.modules.srs.domain.entities import DueCardsPage, QueueStats, Review, SrsCard
from src.app.modules.srs.domain.value_objects import QueueMode


class SrsCardRepository(ABC):
    @abstractmethod
    async def create_card(self, card: SrsCard) -> SrsCard:
        raise NotImplementedError

    @abstractmethod
    async def update_card(self, card: SrsCard) -> SrsCard:
        raise NotImplementedError

    @abstractmethod
    async def get_card_by_id(self, card_id: int, user_id: int) -> SrsCard | None:
        raise NotImplementedError

    @abstractmethod
    async def get_card_by_id_for_update(self, card_id: int, user_id: int) -> SrsCard | None:
        raise NotImplementedError

    @abstractmethod
    async def create_review(self, review: Review) -> Review:
        raise NotImplementedError

    @abstractmethod
    async def save_review_result(self, card: SrsCard, review: Review) -> tuple[SrsCard, Review]:
        raise NotImplementedError

    @abstractmethod
    async def rollback(self) -> None:
        raise NotImplementedError

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
