from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

import httpx
import structlog

from src.app.core.config import settings
from src.app.modules.auth.domain.entities import DataExport, User, UserPreferences
from src.app.modules.auth.domain.exceptions import (
    AccountDeletionError,
    AuthenticationError,
    DataExportNotFoundError,
    InvalidUserPreferencesError,
    UserNotFoundError,
)
from src.app.modules.auth.domain.interfaces import (
    DataExportRepository,
    UserPreferencesRepository,
    UserRepository,
)
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


def build_default_user_preferences(user_id: int) -> UserPreferences:
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

        return build_default_user_preferences(user_id)

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


class DataExportService:
    def __init__(
        self,
        user_repository: UserRepository,
        user_preferences_repository: UserPreferencesRepository,
        data_export_repository: DataExportRepository,
    ) -> None:
        self._user_repository = user_repository
        self._user_preferences_repository = user_preferences_repository
        self._data_export_repository = data_export_repository

    async def request_export(self, user_id: int) -> DataExport:
        user = await self._user_repository.get_by_id(user_id)
        if user is None:
            msg = "User not found"
            raise UserNotFoundError(msg)

        return await self._data_export_repository.create_data_export(
            DataExport(user_id=user_id, status="pending"),
        )

    async def get_export_for_user(self, user_id: int, export_id: int) -> DataExport:
        data_export = await self.get_export_by_id(export_id)
        if data_export.user_id != user_id:
            msg = "Data export not found"
            raise DataExportNotFoundError(msg)

        return await self._expire_if_needed(data_export)

    async def get_export_by_id(self, export_id: int) -> DataExport:
        data_export = await self._data_export_repository.get_data_export_by_id(export_id)
        if data_export is None:
            msg = "Data export not found"
            raise DataExportNotFoundError(msg)

        return data_export

    async def mark_processing(self, export_id: int) -> DataExport:
        data_export = await self.get_export_by_id(export_id)
        return await self._data_export_repository.update_data_export(
            DataExport(
                id=data_export.id,
                user_id=data_export.user_id,
                status="processing",
                file_path=data_export.file_path,
                created_at=data_export.created_at,
                expires_at=data_export.expires_at,
            ),
        )

    async def mark_ready(self, export_id: int, file_path: str, expires_at: datetime) -> DataExport:
        data_export = await self.get_export_by_id(export_id)
        return await self._data_export_repository.update_data_export(
            DataExport(
                id=data_export.id,
                user_id=data_export.user_id,
                status="ready",
                file_path=file_path,
                created_at=data_export.created_at,
                expires_at=expires_at,
            ),
        )

    async def mark_failed(self, export_id: int) -> DataExport:
        data_export = await self.get_export_by_id(export_id)
        return await self._data_export_repository.update_data_export(
            DataExport(
                id=data_export.id,
                user_id=data_export.user_id,
                status="failed",
                file_path=None,
                created_at=data_export.created_at,
                expires_at=None,
            ),
        )

    async def collect_user_data(self, user_id: int) -> dict[str, Any]:
        user = await self._user_repository.get_by_id(user_id)
        if user is None:
            msg = "User not found"
            raise UserNotFoundError(msg)

        preferences = await self._user_preferences_repository.get_by_user_id(user_id)
        current_preferences = preferences or build_default_user_preferences(user_id)

        return {
            "profile": {
                "id": user.id,
                "clerk_id": user.clerk_id,
                "email": user.email,
                "display_name": user.display_name,
                "tier": user.tier.value,
                "created_at": self._serialize_datetime(user.created_at),
                "updated_at": self._serialize_datetime(user.updated_at),
            },
            "preferences": {
                "learning_goal": current_preferences.learning_goal.value,
                "english_level": current_preferences.english_level.value,
                "japanese_level": current_preferences.japanese_level.value,
                "daily_study_minutes": current_preferences.daily_study_minutes,
                "it_domain": current_preferences.it_domain.value,
                "notification_email": current_preferences.notification_email,
                "notification_review_reminder": current_preferences.notification_review_reminder,
                "created_at": self._serialize_datetime(current_preferences.created_at),
                "updated_at": self._serialize_datetime(current_preferences.updated_at),
            },
            "vocabulary_terms": [],
            "review_history": [],
            "learning_patterns": {},
            "collections": [],
            "diagnostics": {},
        }

    def build_export_path(self, user_id: int, export_id: int) -> Path:
        return Path(settings.data_export_storage_path) / str(user_id) / f"{export_id}.zip"

    def build_expiration(self, now: datetime | None = None) -> datetime:
        baseline = now or datetime.now(UTC)
        return baseline + timedelta(days=settings.data_export_ttl_days)

    async def _expire_if_needed(self, data_export: DataExport) -> DataExport:
        if data_export.status != "ready" or data_export.expires_at is None:
            return data_export

        if data_export.expires_at > datetime.now(UTC):
            return data_export

        export_path = Path(data_export.file_path) if data_export.file_path else None
        if export_path and export_path.exists():
            export_path.unlink()

        return await self._data_export_repository.update_data_export(
            DataExport(
                id=data_export.id,
                user_id=data_export.user_id,
                status="expired",
                file_path=None,
                created_at=data_export.created_at,
                expires_at=data_export.expires_at,
            ),
        )

    def _serialize_datetime(self, value: datetime | None) -> str | None:
        return value.isoformat() if value is not None else None


class AccountDeletionService:
    def __init__(
        self,
        user_repository: UserRepository,
        user_preferences_repository: UserPreferencesRepository,
        data_export_repository: DataExportRepository,
    ) -> None:
        self._user_repository = user_repository
        self._user_preferences_repository = user_preferences_repository
        self._data_export_repository = data_export_repository

    async def delete_account(self, user: User, confirmation_email: str) -> None:
        if user.id is None:
            msg = "User not found"
            raise UserNotFoundError(msg)

        if confirmation_email.strip().casefold() != user.email.casefold():
            msg = "Confirmation email does not match current user"
            raise AccountDeletionError(msg)

        existing_user = await self._user_repository.get_by_id(user.id)
        if existing_user is None:
            msg = "User not found"
            raise UserNotFoundError(msg)

        exports = await self._data_export_repository.list_data_exports_by_user_id(user.id)
        for data_export in exports:
            self._delete_export_file(data_export.file_path)

        await self._data_export_repository.delete_data_exports_by_user_id(user.id)
        await self._user_preferences_repository.delete_by_user_id(user.id)
        await self._delete_clerk_user(existing_user.clerk_id)
        await self._user_repository.delete_by_id(user.id)

        logger.info("auth_account_deleted", user_id=user.id)

    def _delete_export_file(self, file_path: str | None) -> None:
        if not file_path:
            return

        export_path = Path(file_path)
        if export_path.exists():
            export_path.unlink()

    async def _delete_clerk_user(self, clerk_user_id: str) -> None:
        if not settings.clerk_secret_key:
            msg = "Clerk secret key is not configured"
            raise AccountDeletionError(msg)

        url = f"https://api.clerk.com/v1/users/{clerk_user_id}"

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.delete(
                    url,
                    headers={"Authorization": f"Bearer {settings.clerk_secret_key}"},
                )
        except httpx.HTTPError as exc:
            msg = "Failed to delete Clerk account"
            raise AccountDeletionError(msg) from exc

        if response.status_code in {200, 204, 404}:
            return

        msg = "Failed to delete Clerk account"
        raise AccountDeletionError(msg, details={"status_code": response.status_code})
