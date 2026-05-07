from abc import ABC, abstractmethod
from datetime import datetime
from typing import TypedDict
from uuid import UUID

from src.app.modules.dashboard.domain.entities import DiagnosticInsight


class ReviewAnalyticsRow(TypedDict):
    card_id: int
    reviewed_at: datetime
    rating: int
    response_time_ms: int | None
    language: str
    parallel_mode_active: bool | None
    term_id: int | None
    term_category: str | None
    term_text: str | None


class DiagnosticRepository(ABC):
    @abstractmethod
    async def get_pending_insights(
        self,
        user_id: int,
        session_id: UUID,
        limit: int,
    ) -> list[DiagnosticInsight]:
        raise NotImplementedError

    @abstractmethod
    async def mark_insight_seen(
        self,
        insight_id: int,
        user_id: int,
        session_id: UUID,
    ) -> None:
        raise NotImplementedError

    @abstractmethod
    async def get_review_analytics(
        self,
        user_id: int,
        days_back: int,
    ) -> list[ReviewAnalyticsRow]:
        raise NotImplementedError

    @abstractmethod
    async def count_active_insights(self, user_id: int) -> int:
        raise NotImplementedError

    @abstractmethod
    async def replace_insights(
        self,
        user_id: int,
        insights: list[DiagnosticInsight],
    ) -> None:
        raise NotImplementedError
