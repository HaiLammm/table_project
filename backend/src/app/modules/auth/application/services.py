from dataclasses import dataclass, field

import structlog

from src.app.modules.auth.domain.entities import User, UserPreferences
from src.app.modules.auth.domain.exceptions import AuthenticationError, InvalidUserPreferencesError
from src.app.modules.auth.domain.interfaces import UserPreferencesRepository, UserRepository
from src.app.modules.auth.domain.value_objects import (
    ALLOWED_DAILY_STUDY_MINUTES,
    DEFAULT_DAILY_STUDY_MINUTES,
    DEFAULT_ENGLISH_LEVEL,
    DEFAULT_IT_DOMAIN,
    DEFAULT_JAPANESE_LEVEL,
    DEFAULT_LEARNING_GOAL,
    DEFAULT_NOTIFICATION_EMAIL,
    DEFAULT_NOTIFICATION_REVIEW_REMINDER,
    EnglishLevel,
    ITDomain,
    JapaneseLevel,
    LearningGoal,
    UserTier,
)

logger = structlog.get_logger().bind(module="auth_service")


@dataclass(slots=True, kw_only=True)
class ClerkEmailAddress:
    email_address: str
    id: str | None = None


@dataclass(slots=True, kw_only=True)
class ClerkUserSyncPayload:
    event_type: str
    clerk_id: str
    email_addresses: list[ClerkEmailAddress] = field(default_factory=list)
    primary_email_address_id: str | None = None
    first_name: str | None = None
    last_name: str | None = None
    username: str | None = None


@dataclass(slots=True, kw_only=True)
class UserPreferencesUpdateInput:
    learning_goal: LearningGoal | None = None
    english_level: EnglishLevel | None = None
    japanese_level: JapaneseLevel | None = None
    daily_study_minutes: int | None = None
    it_domain: ITDomain | None = None
    notification_email: bool | None = None
    notification_review_reminder: bool | None = None


class UserSyncService:
    def __init__(self, user_repository: UserRepository) -> None:
        self._user_repository = user_repository

    async def sync_from_clerk_webhook(self, payload: ClerkUserSyncPayload) -> User | None:
        if payload.event_type == "user.deleted":
            logger.info("auth_user_delete_ignored", clerk_id=payload.clerk_id)
            return None

        existing_user = await self._user_repository.get_by_clerk_id(payload.clerk_id)
        email = self._resolve_email(payload, existing_user)
        display_name = self._resolve_display_name(payload, existing_user, email)

        if existing_user is None:
            logger.info("auth_user_sync_create", clerk_id=payload.clerk_id)
            return await self._user_repository.create(
                User(
                    clerk_id=payload.clerk_id,
                    email=email,
                    display_name=display_name,
                    tier=UserTier.FREE,
                ),
            )

        logger.info("auth_user_sync_update", clerk_id=payload.clerk_id)
        return await self._user_repository.update(
            User(
                id=existing_user.id,
                clerk_id=payload.clerk_id,
                email=email,
                display_name=display_name,
                tier=existing_user.tier,
                created_at=existing_user.created_at,
                updated_at=existing_user.updated_at,
            ),
        )

    def _resolve_email(self, payload: ClerkUserSyncPayload, existing_user: User | None) -> str:
        email = self._select_primary_email(payload)
        if email is not None:
            return email

        if existing_user is not None:
            return existing_user.email

        msg = "Clerk user payload does not include an email address"
        raise AuthenticationError(msg, details={"clerk_id": payload.clerk_id})

    def _resolve_display_name(
        self,
        payload: ClerkUserSyncPayload,
        existing_user: User | None,
        email: str,
    ) -> str:
        full_name = " ".join(
            value.strip()
            for value in [payload.first_name, payload.last_name]
            if value and value.strip()
        )
        if full_name:
            return full_name

        if payload.username:
            return payload.username

        if existing_user and existing_user.display_name:
            return existing_user.display_name

        return email.split("@", maxsplit=1)[0]

    def _select_primary_email(self, payload: ClerkUserSyncPayload) -> str | None:
        if payload.primary_email_address_id:
            for email in payload.email_addresses:
                if email.id == payload.primary_email_address_id:
                    return email.email_address

        if payload.email_addresses:
            return payload.email_addresses[0].email_address

        return None


class UserPreferencesService:
    def __init__(self, user_preferences_repository: UserPreferencesRepository) -> None:
        self._user_preferences_repository = user_preferences_repository

    async def get_preferences(self, user_id: int) -> UserPreferences:
        preferences = await self._user_preferences_repository.get_by_user_id(user_id)
        if preferences is not None:
            return preferences

        return self._build_default_preferences(user_id)

    async def update_preferences(
        self,
        user_id: int,
        updates: UserPreferencesUpdateInput,
    ) -> UserPreferences:
        self._validate_daily_study_minutes(updates.daily_study_minutes)

        current_preferences = await self.get_preferences(user_id)
        next_preferences = UserPreferences(
            id=current_preferences.id,
            user_id=user_id,
            learning_goal=updates.learning_goal or current_preferences.learning_goal,
            english_level=updates.english_level or current_preferences.english_level,
            japanese_level=updates.japanese_level or current_preferences.japanese_level,
            daily_study_minutes=updates.daily_study_minutes
            or current_preferences.daily_study_minutes,
            it_domain=updates.it_domain or current_preferences.it_domain,
            notification_email=(
                updates.notification_email
                if updates.notification_email is not None
                else current_preferences.notification_email
            ),
            notification_review_reminder=(
                updates.notification_review_reminder
                if updates.notification_review_reminder is not None
                else current_preferences.notification_review_reminder
            ),
            created_at=current_preferences.created_at,
            updated_at=current_preferences.updated_at,
        )
        return await self._user_preferences_repository.upsert(next_preferences)

    def _build_default_preferences(self, user_id: int) -> UserPreferences:
        return UserPreferences(
            user_id=user_id,
            learning_goal=DEFAULT_LEARNING_GOAL,
            english_level=DEFAULT_ENGLISH_LEVEL,
            japanese_level=DEFAULT_JAPANESE_LEVEL,
            daily_study_minutes=DEFAULT_DAILY_STUDY_MINUTES,
            it_domain=DEFAULT_IT_DOMAIN,
            notification_email=DEFAULT_NOTIFICATION_EMAIL,
            notification_review_reminder=DEFAULT_NOTIFICATION_REVIEW_REMINDER,
        )

    def _validate_daily_study_minutes(self, daily_study_minutes: int | None) -> None:
        if daily_study_minutes is None:
            return

        if daily_study_minutes not in ALLOWED_DAILY_STUDY_MINUTES:
            msg = "Invalid daily study minutes value"
            raise InvalidUserPreferencesError(
                msg,
                details={
                    "daily_study_minutes": daily_study_minutes,
                    "allowed_values": sorted(ALLOWED_DAILY_STUDY_MINUTES),
                },
            )
