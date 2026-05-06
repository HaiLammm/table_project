from datetime import UTC, datetime

import pytest

from src.app.modules.auth.application.services import (
    UserPreferencesService,
    UserPreferencesUpdateInput,
)
from src.app.modules.auth.domain.entities import UserPreferences
from src.app.modules.auth.domain.exceptions import InvalidUserPreferencesError
from src.app.modules.auth.domain.interfaces import UserPreferencesRepository
from src.app.modules.auth.domain.value_objects import (
    EnglishLevel,
    ITDomain,
    JapaneseLevel,
    LearningGoal,
)


class InMemoryUserPreferencesRepository(UserPreferencesRepository):
    def __init__(self, existing_preferences: UserPreferences | None = None) -> None:
        self._existing_preferences = existing_preferences
        self.saved_preferences: UserPreferences | None = None

    async def get_by_user_id(self, user_id: int) -> UserPreferences | None:
        if self._existing_preferences and self._existing_preferences.user_id == user_id:
            return self._existing_preferences

        return None

    async def upsert(self, preferences: UserPreferences) -> UserPreferences:
        saved_preferences = UserPreferences(
            id=preferences.id or 1,
            user_id=preferences.user_id,
            learning_goal=preferences.learning_goal,
            english_level=preferences.english_level,
            japanese_level=preferences.japanese_level,
            daily_study_minutes=preferences.daily_study_minutes,
            it_domain=preferences.it_domain,
            notification_email=preferences.notification_email,
            notification_review_reminder=preferences.notification_review_reminder,
            created_at=preferences.created_at or datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )
        self.saved_preferences = saved_preferences
        self._existing_preferences = saved_preferences
        return saved_preferences

    async def delete_by_user_id(self, user_id: int) -> None:
        if self._existing_preferences and self._existing_preferences.user_id == user_id:
            self._existing_preferences = None


async def test_get_preferences_returns_defaults_when_missing() -> None:
    repository = InMemoryUserPreferencesRepository()
    service = UserPreferencesService(repository)

    preferences = await service.get_preferences(user_id=7)

    assert preferences.user_id == 7
    assert preferences.learning_goal is LearningGoal.GENERAL
    assert preferences.english_level is EnglishLevel.BEGINNER
    assert preferences.japanese_level is JapaneseLevel.NONE
    assert preferences.daily_study_minutes == 15
    assert preferences.it_domain is ITDomain.GENERAL_IT
    assert preferences.notification_email is True
    assert preferences.notification_review_reminder is True
    assert preferences.id is None


async def test_update_preferences_creates_defaults_and_merges_partial_updates() -> None:
    repository = InMemoryUserPreferencesRepository()
    service = UserPreferencesService(repository)

    preferences = await service.update_preferences(
        user_id=7,
        updates=UserPreferencesUpdateInput(
            learning_goal=LearningGoal.WORKPLACE,
            english_level=EnglishLevel.INTERMEDIATE,
            japanese_level=JapaneseLevel.N4,
            daily_study_minutes=30,
            notification_review_reminder=False,
        ),
    )

    assert repository.saved_preferences is not None
    assert preferences.user_id == 7
    assert preferences.learning_goal is LearningGoal.WORKPLACE
    assert preferences.english_level is EnglishLevel.INTERMEDIATE
    assert preferences.japanese_level is JapaneseLevel.N4
    assert preferences.daily_study_minutes == 30
    assert preferences.it_domain is ITDomain.GENERAL_IT
    assert preferences.notification_email is True
    assert preferences.notification_review_reminder is False


async def test_update_preferences_rejects_invalid_daily_study_minutes() -> None:
    repository = InMemoryUserPreferencesRepository()
    service = UserPreferencesService(repository)

    with pytest.raises(InvalidUserPreferencesError, match="daily study minutes"):
        await service.update_preferences(
            user_id=7,
            updates=UserPreferencesUpdateInput(daily_study_minutes=20),
        )
