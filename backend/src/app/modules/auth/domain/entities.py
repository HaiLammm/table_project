from dataclasses import dataclass
from datetime import datetime

from src.app.modules.auth.domain.value_objects import (
    EnglishLevel,
    ITDomain,
    JapaneseLevel,
    LearningGoal,
    UserTier,
)


@dataclass(slots=True, kw_only=True)
class User:
    clerk_id: str
    email: str
    display_name: str | None
    tier: UserTier = UserTier.FREE
    id: int | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None


@dataclass(slots=True, kw_only=True)
class UserPreferences:
    user_id: int
    learning_goal: LearningGoal
    english_level: EnglishLevel
    japanese_level: JapaneseLevel
    daily_study_minutes: int
    it_domain: ITDomain
    notification_email: bool
    notification_review_reminder: bool
    id: int | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None


@dataclass(slots=True, kw_only=True)
class DataExport:
    user_id: int
    status: str
    id: int | None = None
    file_path: str | None = None
    created_at: datetime | None = None
    expires_at: datetime | None = None
