from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum

from src.app.modules.dashboard.domain.value_objects import PatternType


class InsightSeverity(StrEnum):
    INFO = "info"
    WARNING = "warning"
    SUCCESS = "success"


@dataclass(slots=True, kw_only=True)
class DiagnosticInsight:
    user_id: int
    type: PatternType
    severity: InsightSeverity
    icon: str
    title: str
    text: str
    confidence_score: float
    id: int | None = None
    action_label: str | None = None
    action_href: str | None = None
    created_at: datetime | None = None
    expires_at: datetime | None = None

    def __post_init__(self) -> None:
        if not (0.0 <= self.confidence_score <= 1.0):
            msg = f"confidence_score must be between 0.0 and 1.0, got {self.confidence_score}"
            raise ValueError(msg)

    @property
    def delivery_interval(self) -> int:
        if self.confidence_score <= 0.5:
            return 10
        if self.confidence_score < 1.0:
            return 7
        return 5
