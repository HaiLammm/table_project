from dataclasses import dataclass, field
from datetime import datetime
from uuid import UUID

from src.app.modules.srs.domain.value_objects import QueueMode, Rating


@dataclass(slots=True, kw_only=True)
class SrsCard:
    user_id: int
    due_at: datetime
    language: str
    id: int | None = None
    term_id: int | None = None
    fsrs_state: dict[str, object] = field(default_factory=dict)
    stability: float | None = None
    difficulty: float | None = None
    reps: int = 0
    lapses: int = 0
    created_at: datetime | None = None
    updated_at: datetime | None = None


@dataclass(slots=True, kw_only=True)
class Review:
    card_id: int
    user_id: int
    rating: Rating
    reviewed_at: datetime
    id: int | None = None
    response_time_ms: int | None = None
    session_id: UUID | None = None
    previous_fsrs_state: dict[str, object] | None = None
    previous_stability: float | None = None
    previous_difficulty: float | None = None
    previous_reps: int | None = None
    previous_lapses: int | None = None


@dataclass(slots=True, kw_only=True)
class ReviewResult:
    card: SrsCard
    reviewed_at: datetime
    next_due_at: datetime
    interval_display: str


@dataclass(slots=True, kw_only=True)
class QueueStats:
    due_count: int
    overdue_count: int
    estimated_minutes: int

    @property
    def has_overdue(self) -> bool:
        return self.overdue_count > 0


@dataclass(slots=True, kw_only=True)
class SessionStats:
    cards_reviewed: int
    cards_graduated: int
    cards_lapsed: int
    lapsed_card_ids: list[int]
    tomorrow_due_count: int
    tomorrow_estimated_minutes: int


@dataclass(slots=True, kw_only=True)
class SessionReviewRow:
    card_id: int
    rating: int
    previous_stability: float | None
    current_card_stability: float | None


@dataclass(slots=True, kw_only=True)
class DueCardsPage:
    items: list[SrsCard]
    total_count: int
    mode: QueueMode
    limit: int
    offset: int
