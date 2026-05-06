from datetime import datetime

from pydantic import BaseModel, ConfigDict

from src.app.modules.srs.domain.value_objects import QueueMode


class QueueStatsResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    due_count: int
    estimated_minutes: int
    has_overdue: bool
    overdue_count: int


class DueCardResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    term_id: int | None = None
    due_at: datetime
    fsrs_state: dict[str, object]


class DueCardsResponse(BaseModel):
    items: list[DueCardResponse]
    total_count: int
    limit: int
    offset: int
    mode: QueueMode
