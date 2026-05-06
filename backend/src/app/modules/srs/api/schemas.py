from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from src.app.modules.srs.domain.value_objects import QueueMode


class QueueStatsResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    due_count: int
    estimated_minutes: int
    has_overdue: bool
    overdue_count: int


class SrsCardResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    term_id: int | None = None
    language: Literal["en", "jp"]
    due_at: datetime
    fsrs_state: dict[str, object]
    stability: float | None = None
    difficulty: float | None = None
    reps: int
    lapses: int


class CreateSrsCardRequest(BaseModel):
    term_id: int
    language: Literal["en", "jp"]


class CreateSrsCardResponse(SrsCardResponse):
    pass


class ReviewCardRequest(BaseModel):
    rating: int = Field(ge=1, le=4)
    response_time_ms: int | None = Field(default=None, ge=0)
    session_id: UUID | None = None


class ReviewCardResponse(SrsCardResponse):
    next_due_at: datetime
    interval_display: str


class DueCardResponse(SrsCardResponse):
    pass


class DueCardsResponse(BaseModel):
    items: list[DueCardResponse]
    total_count: int
    limit: int
    offset: int
    mode: QueueMode
