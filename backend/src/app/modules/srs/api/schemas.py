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
    retention_rate: float | None = None


class CreateCardsForCollectionRequest(BaseModel):
    collection_id: int
    language: str = "en"


class CreateCardsForCollectionResponse(BaseModel):
    created_count: int
    skipped_count: int


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
    session_length_s: int | None = Field(default=None, ge=0)
    parallel_mode_active: bool = False
    session_id: UUID | None = None


class ReviewCardResponse(SrsCardResponse):
    next_due_at: datetime
    interval_display: str


class EmbeddedTermResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    term: str
    language: str
    cefr_level: str | None = None
    jlpt_level: str | None = None
    part_of_speech: str | None = None
    definitions: list[dict[str, object]] = []


class DueCardResponse(SrsCardResponse):
    term: EmbeddedTermResponse | None = None


class DueCardsResponse(BaseModel):
    items: list[DueCardResponse]
    total_count: int
    limit: int
    offset: int
    mode: QueueMode


class UndoReviewResponse(SrsCardResponse):
    next_due_at: datetime
    interval_display: str
    stability: float | None = None
    difficulty: float | None = None
    reps: int
    lapses: int


class SessionStatsResponse(BaseModel):
    cards_reviewed: int
    cards_graduated: int
    cards_lapsed: int
    lapsed_card_ids: list[int]
    tomorrow_due_count: int
    tomorrow_estimated_minutes: int


class ScheduleBucketResponse(BaseModel):
    due_count: int
    estimated_minutes: int


class UpcomingScheduleResponse(BaseModel):
    today: ScheduleBucketResponse
    tomorrow: ScheduleBucketResponse
    this_week: ScheduleBucketResponse
