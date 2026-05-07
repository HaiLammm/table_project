from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from src.app.modules.dashboard.domain.value_objects import PatternType


class InsightResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    type: PatternType
    severity: Literal["info", "warning", "success"]
    icon: str
    title: str
    text: str
    action_label: str | None = None
    action_href: str | None = None
    delivery_interval: int


class PendingInsightsResponse(BaseModel):
    items: list[InsightResponse]


class MarkInsightSeenRequest(BaseModel):
    session_id: UUID


class SuccessResponse(BaseModel):
    success: bool = Field(default=True)
