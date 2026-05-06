from datetime import UTC, datetime

from src.app.modules.auth.application.services import (
    ClerkEmailAddress,
    ClerkUserSyncPayload,
    UserSyncService,
)
from src.app.modules.auth.domain.entities import User
from src.app.modules.auth.domain.interfaces import UserRepository
from src.app.modules.auth.domain.value_objects import UserTier


class InMemoryUserRepository(UserRepository):
    def __init__(self, existing_user: User | None = None) -> None:
        self._existing_user = existing_user
        self.created_user: User | None = None
        self.updated_user: User | None = None

    async def get_by_clerk_id(self, clerk_id: str) -> User | None:
        if self._existing_user and self._existing_user.clerk_id == clerk_id:
            return self._existing_user

        return None

    async def get_by_id(self, user_id: int) -> User | None:
        if self._existing_user and self._existing_user.id == user_id:
            return self._existing_user

        return None

    async def create(self, user: User) -> User:
        self.created_user = User(
            id=1,
            clerk_id=user.clerk_id,
            email=user.email,
            display_name=user.display_name,
            tier=user.tier,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )
        return self.created_user

    async def update(self, user: User) -> User:
        self.updated_user = User(
            id=user.id,
            clerk_id=user.clerk_id,
            email=user.email,
            display_name=user.display_name,
            tier=user.tier,
            created_at=user.created_at,
            updated_at=datetime.now(UTC),
        )
        return self.updated_user


async def test_sync_from_clerk_webhook_creates_user_from_primary_email() -> None:
    repository = InMemoryUserRepository()
    service = UserSyncService(repository)

    synced_user = await service.sync_from_clerk_webhook(
        ClerkUserSyncPayload(
            event_type="user.created",
            clerk_id="user_123",
            email_addresses=[
                ClerkEmailAddress(
                    id="email_123",
                    email_address="lem@example.com",
                ),
            ],
            primary_email_address_id="email_123",
            first_name="Lem",
            last_name="Nguyen",
        ),
    )

    assert synced_user is not None
    assert repository.created_user is not None
    assert synced_user.clerk_id == "user_123"
    assert synced_user.email == "lem@example.com"
    assert synced_user.display_name == "Lem Nguyen"
    assert synced_user.tier is UserTier.FREE


async def test_sync_from_clerk_webhook_updates_existing_user() -> None:
    existing_user = User(
        id=7,
        clerk_id="user_123",
        email="old@example.com",
        display_name="Old Name",
        tier=UserTier.STUDENT,
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )
    repository = InMemoryUserRepository(existing_user=existing_user)
    service = UserSyncService(repository)

    synced_user = await service.sync_from_clerk_webhook(
        ClerkUserSyncPayload(
            event_type="user.updated",
            clerk_id="user_123",
            email_addresses=[
                ClerkEmailAddress(
                    id="email_456",
                    email_address="new@example.com",
                ),
            ],
            primary_email_address_id="email_456",
            username="lem-updated",
        ),
    )

    assert synced_user is not None
    assert repository.updated_user is not None
    assert synced_user.id == existing_user.id
    assert synced_user.email == "new@example.com"
    assert synced_user.display_name == "lem-updated"
    assert synced_user.tier is UserTier.STUDENT


async def test_sync_from_clerk_webhook_ignores_deleted_events() -> None:
    repository = InMemoryUserRepository()
    service = UserSyncService(repository)

    synced_user = await service.sync_from_clerk_webhook(
        ClerkUserSyncPayload(
            event_type="user.deleted",
            clerk_id="user_123",
        ),
    )

    assert synced_user is None
    assert repository.created_user is None
    assert repository.updated_user is None
