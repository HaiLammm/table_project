from dataclasses import dataclass, field
from datetime import datetime

from src.app.modules.srs.domain.value_objects import QueueMode


@dataclass(slots=True, kw_only=True)
class SrsCard:
    user_id: int
    due_at: datetime
    id: int | None = None
    term_id: int | None = None
    fsrs_state: dict[str, object] = field(default_factory=dict)
    created_at: datetime | None = None
    updated_at: datetime | None = None


@dataclass(slots=True, kw_only=True)
class QueueStats:
    due_count: int
    overdue_count: int
    estimated_minutes: int

    @property
    def has_overdue(self) -> bool:
        return self.overdue_count > 0


@dataclass(slots=True, kw_only=True)
class DueCardsPage:
    items: list[SrsCard]
    total_count: int
    mode: QueueMode
    limit: int
    offset: int
