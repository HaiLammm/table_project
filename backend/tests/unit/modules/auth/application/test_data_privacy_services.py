from datetime import UTC, datetime, timedelta
from pathlib import Path

import httpx
import pytest

from src.app.core.config import settings
from src.app.modules.auth.application.services import AccountDeletionService, DataExportService
from src.app.modules.auth.domain.entities import DataExport, User, UserPreferences
from src.app.modules.auth.domain.exceptions import AccountDeletionError
from src.app.modules.auth.domain.interfaces import (
    DataExportRepository,
    UserPreferencesRepository,
    UserRepository,
)
from src.app.modules.auth.domain.value_objects import (
    EnglishLevel,
    ITDomain,
    JapaneseLevel,
    LearningGoal,
    UserTier,
)


class InMemoryPrivacyRepository(UserRepository, UserPreferencesRepository, DataExportRepository):
    def __init__(
        self,
        *,
        user: User | None = None,
        preferences: UserPreferences | None = None,
        exports: list[DataExport] | None = None,
    ) -> None:
        self.user = user
        self.preferences = preferences
        self.exports = {data_export.id or 0: data_export for data_export in exports or []}
        self.next_export_id = max(self.exports, default=0) + 1
        self.deleted_user_id: int | None = None
        self.deleted_preferences_user_id: int | None = None
        self.deleted_exports_user_id: int | None = None

    async def get_by_clerk_id(self, clerk_id: str) -> User | None:
        if self.user and self.user.clerk_id == clerk_id:
            return self.user

        return None

    async def get_by_id(self, user_id: int) -> User | None:
        if self.user and self.user.id == user_id:
            return self.user

        return None

    async def create(self, user: User) -> User:
        self.user = User(
            id=1,
            clerk_id=user.clerk_id,
            email=user.email,
            display_name=user.display_name,
            tier=user.tier,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )
        return self.user

    async def update(self, user: User) -> User:
        self.user = user
        return user

    async def delete_by_id(self, user_id: int) -> None:
        self.deleted_user_id = user_id
        self.user = None

    async def get_by_user_id(self, user_id: int) -> UserPreferences | None:
        if self.preferences and self.preferences.user_id == user_id:
            return self.preferences

        return None

    async def upsert(self, preferences: UserPreferences) -> UserPreferences:
        self.preferences = preferences
        return preferences

    async def delete_by_user_id(self, user_id: int) -> None:
        self.deleted_preferences_user_id = user_id
        self.preferences = None

    async def create_data_export(self, data_export: DataExport) -> DataExport:
        saved_export = DataExport(
            id=self.next_export_id,
            user_id=data_export.user_id,
            status=data_export.status,
            file_path=data_export.file_path,
            created_at=datetime.now(UTC),
            expires_at=data_export.expires_at,
        )
        assert saved_export.id is not None
        self.exports[saved_export.id] = saved_export
        self.next_export_id += 1
        return saved_export

    async def get_data_export_by_id(self, export_id: int) -> DataExport | None:
        return self.exports.get(export_id)

    async def list_data_exports_by_user_id(self, user_id: int) -> list[DataExport]:
        return [
            data_export for data_export in self.exports.values() if data_export.user_id == user_id
        ]

    async def update_data_export(self, data_export: DataExport) -> DataExport:
        assert data_export.id is not None
        self.exports[data_export.id] = data_export
        return data_export

    async def delete_data_exports_by_user_id(self, user_id: int) -> None:
        self.deleted_exports_user_id = user_id
        self.exports = {
            export_id: data_export
            for export_id, data_export in self.exports.items()
            if data_export.user_id != user_id
        }


class FakeDeleteResponse:
    def __init__(self, status_code: int) -> None:
        self.status_code = status_code


class FakeAsyncClient:
    def __init__(self, *, status_code: int = 204) -> None:
        self.status_code = status_code
        self.calls: list[tuple[str, dict[str, str]]] = []

    async def __aenter__(self) -> "FakeAsyncClient":
        return self

    async def __aexit__(self, exc_type: object, exc: object, tb: object) -> None:
        _ = (exc_type, exc, tb)

    async def delete(self, url: str, headers: dict[str, str]) -> FakeDeleteResponse:
        self.calls.append((url, headers))
        return FakeDeleteResponse(self.status_code)


async def test_data_export_service_collects_profile_preferences_and_placeholders() -> None:
    repository = InMemoryPrivacyRepository(
        user=User(
            id=7,
            clerk_id="user_123",
            email="lem@example.com",
            display_name="Lem",
            tier=UserTier.FREE,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        ),
        preferences=UserPreferences(
            id=3,
            user_id=7,
            learning_goal=LearningGoal.WORKPLACE,
            english_level=EnglishLevel.INTERMEDIATE,
            japanese_level=JapaneseLevel.N4,
            daily_study_minutes=30,
            it_domain=ITDomain.BACKEND,
            notification_email=False,
            notification_review_reminder=True,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        ),
    )
    service = DataExportService(repository, repository, repository)

    export_request = await service.request_export(7)
    payload = await service.collect_user_data(7)

    assert export_request.id is not None
    assert export_request.status == "pending"
    assert payload["profile"]["email"] == "lem@example.com"
    assert payload["preferences"]["it_domain"] == "backend"
    assert payload["vocabulary_terms"] == []
    assert payload["review_history"] == []
    assert payload["learning_patterns"] == {}
    assert payload["collections"] == []
    assert payload["diagnostics"] == {}


async def test_data_export_service_marks_ready_exports_as_expired(tmp_path: Path) -> None:
    export_file = tmp_path / "exports" / "1.zip"
    export_file.parent.mkdir(parents=True, exist_ok=True)
    export_file.write_bytes(b"zip-data")

    repository = InMemoryPrivacyRepository(
        user=User(
            id=7,
            clerk_id="user_123",
            email="lem@example.com",
            display_name="Lem",
            tier=UserTier.FREE,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        ),
        exports=[
            DataExport(
                id=1,
                user_id=7,
                status="ready",
                file_path=str(export_file),
                created_at=datetime.now(UTC) - timedelta(days=8),
                expires_at=datetime.now(UTC) - timedelta(minutes=1),
            ),
        ],
    )
    service = DataExportService(repository, repository, repository)

    expired_export = await service.get_export_for_user(7, 1)

    assert expired_export.status == "expired"
    assert expired_export.file_path is None
    assert not export_file.exists()


async def test_account_deletion_service_removes_local_data_and_deletes_clerk_user(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    export_file = tmp_path / "exports" / "7.zip"
    export_file.parent.mkdir(parents=True, exist_ok=True)
    export_file.write_text("secret-data", encoding="utf-8")

    repository = InMemoryPrivacyRepository(
        user=User(
            id=7,
            clerk_id="user_123",
            email="lem@example.com",
            display_name="Lem",
            tier=UserTier.FREE,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        ),
        preferences=UserPreferences(
            id=3,
            user_id=7,
            learning_goal=LearningGoal.WORKPLACE,
            english_level=EnglishLevel.INTERMEDIATE,
            japanese_level=JapaneseLevel.N4,
            daily_study_minutes=30,
            it_domain=ITDomain.BACKEND,
            notification_email=False,
            notification_review_reminder=True,
        ),
        exports=[
            DataExport(
                id=1,
                user_id=7,
                status="ready",
                file_path=str(export_file),
                created_at=datetime.now(UTC),
            ),
        ],
    )
    service = AccountDeletionService(repository, repository, repository)
    http_client = FakeAsyncClient()

    monkeypatch.setattr(settings, "clerk_secret_key", "sk_test_123")
    monkeypatch.setattr(httpx, "AsyncClient", lambda timeout: http_client)

    await service.delete_account(
        User(
            id=7,
            clerk_id="user_123",
            email="lem@example.com",
            display_name="Lem",
            tier=UserTier.FREE,
        ),
        "lem@example.com",
    )

    assert repository.deleted_exports_user_id == 7
    assert repository.deleted_preferences_user_id == 7
    assert repository.deleted_user_id == 7
    assert repository.user is None
    assert repository.preferences is None
    assert repository.exports == {}
    assert not export_file.exists()
    assert http_client.calls == [
        (
            "https://api.clerk.com/v1/users/user_123",
            {"Authorization": "Bearer sk_test_123"},
        ),
    ]


async def test_account_deletion_service_rejects_mismatched_confirmation_email() -> None:
    repository = InMemoryPrivacyRepository(
        user=User(
            id=7,
            clerk_id="user_123",
            email="lem@example.com",
            display_name="Lem",
            tier=UserTier.FREE,
        ),
    )
    service = AccountDeletionService(repository, repository, repository)
    assert repository.user is not None

    with pytest.raises(AccountDeletionError, match="Confirmation email"):
        await service.delete_account(repository.user, "wrong@example.com")
