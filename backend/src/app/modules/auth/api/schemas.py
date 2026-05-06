from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from src.app.modules.auth.domain.value_objects import (
    EnglishLevel,
    ITDomain,
    JapaneseLevel,
    LearningGoal,
    UserTier,
)

DailyStudyMinutes = Literal[5, 15, 30, 60]


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    clerk_id: str
    email: str
    display_name: str | None
    tier: UserTier
    created_at: datetime
    updated_at: datetime


class ClerkEmailAddressPayload(BaseModel):
    id: str | None = None
    email_address: str


class ClerkWebhookUserPayload(BaseModel):
    id: str
    email_addresses: list[ClerkEmailAddressPayload] = Field(default_factory=list)
    primary_email_address_id: str | None = None
    first_name: str | None = None
    last_name: str | None = None
    username: str | None = None


class WebhookPayload(BaseModel):
    type: Literal["user.created", "user.updated", "user.deleted"]
    data: ClerkWebhookUserPayload


class WebhookSyncResponse(BaseModel):
    status: Literal["synced", "ignored"]
    event_type: Literal["user.created", "user.updated", "user.deleted"]
    user: UserResponse | None = None


class UserPreferencesUpdateRequest(BaseModel):
    learning_goal: LearningGoal | None = None
    english_level: EnglishLevel | None = None
    japanese_level: JapaneseLevel | None = None
    daily_study_minutes: DailyStudyMinutes | None = None
    it_domain: ITDomain | None = None
    notification_email: bool | None = None
    notification_review_reminder: bool | None = None


class UserPreferencesResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    learning_goal: LearningGoal
    english_level: EnglishLevel
    japanese_level: JapaneseLevel
    daily_study_minutes: DailyStudyMinutes
    it_domain: ITDomain
    notification_email: bool
    notification_review_reminder: bool
