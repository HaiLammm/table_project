from abc import ABC, abstractmethod
from datetime import datetime
from uuid import UUID

from src.app.modules.srs.domain.entities import (
    DueCardsPage,
    QueueStats,
    Review,
    SessionReviewRow,
    SrsCard,
    UpcomingSchedule,
)
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
    async def get_last_review(self, card_id: int, user_id: int) -> Review | None:
        raise NotImplementedError

    @abstractmethod
    async def get_last_review_for_update(self, card_id: int, user_id: int) -> Review | None:
        raise NotImplementedError

    @abstractmethod
    async def delete_review(self, review_id: int) -> None:
        raise NotImplementedError

    @abstractmethod
    async def update_card_with_delete_review(self, card: SrsCard, review_id: int) -> SrsCard:
        raise NotImplementedError

    @abstractmethod
    async def rollback(self) -> None:
        raise NotImplementedError

    @abstractmethod
    async def get_queue_stats(
        self, user_id: int, now: datetime, collection_id: int | None = None
    ) -> QueueStats:
        raise NotImplementedError

    @abstractmethod
    async def list_due_cards(
        self,
        user_id: int,
        now: datetime,
        mode: QueueMode,
        limit: int,
        offset: int,
        collection_id: int | None = None,
    ) -> DueCardsPage:
        raise NotImplementedError

    @abstractmethod
    async def get_session_reviews(self, user_id: int, session_id: UUID) -> list[SessionReviewRow]:
        raise NotImplementedError

    @abstractmethod
    async def count_due_cards_for_date(self, user_id: int, date_end: datetime) -> int:
        raise NotImplementedError

    @abstractmethod
    async def find_term_ids_without_cards(
        self, user_id: int, collection_id: int, language: str
    ) -> list[int]:
        raise NotImplementedError

    @abstractmethod
    async def count_due_cards_by_buckets(
        self, user_id: int, today_end: datetime, tomorrow_end: datetime, week_end: datetime
    ) -> UpcomingSchedule:
        raise NotImplementedError
