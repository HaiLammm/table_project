from dataclasses import dataclass, field

import structlog

from src.app.modules.auth.domain.entities import User
from src.app.modules.auth.domain.exceptions import AuthenticationError
from src.app.modules.auth.domain.interfaces import UserRepository
from src.app.modules.auth.domain.value_objects import UserTier

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
