from typing import Annotated

import structlog
from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession
from svix.webhooks import Webhook, WebhookVerificationError

from src.app.core.config import settings
from src.app.db.session import get_async_session
from src.app.modules.auth.api.dependencies import get_current_user as get_authenticated_user
from src.app.modules.auth.api.schemas import UserResponse, WebhookPayload, WebhookSyncResponse
from src.app.modules.auth.application.services import (
    ClerkEmailAddress,
    ClerkUserSyncPayload,
    UserSyncService,
)
from src.app.modules.auth.domain.entities import User
from src.app.modules.auth.domain.exceptions import AuthenticationError, AuthorizationError
from src.app.modules.auth.infrastructure.repository import SqlAlchemyUserRepository

logger = structlog.get_logger().bind(module="auth_api")
router = APIRouter()
SessionDependency = Annotated[AsyncSession, Depends(get_async_session)]


def get_user_sync_service(
    session: SessionDependency,
) -> UserSyncService:
    return UserSyncService(SqlAlchemyUserRepository(session))


CurrentUserDependency = Annotated[User, Depends(get_authenticated_user)]
UserSyncServiceDependency = Annotated[UserSyncService, Depends(get_user_sync_service)]


@router.get("/users/me", response_model=UserResponse, tags=["users"])
async def read_current_user(
    current_user: CurrentUserDependency,
) -> UserResponse:
    return UserResponse.model_validate(current_user)


@router.post("/auth/webhook", response_model=WebhookSyncResponse, tags=["auth"])
async def handle_clerk_webhook(
    request: Request,
    user_sync_service: UserSyncServiceDependency,
) -> WebhookSyncResponse:
    if not settings.clerk_webhook_secret:
        msg = "Clerk webhook secret is not configured"
        raise AuthenticationError(msg)

    webhook_headers = {
        "svix-id": request.headers.get("svix-id") or "",
        "svix-timestamp": request.headers.get("svix-timestamp") or "",
        "svix-signature": request.headers.get("svix-signature") or "",
    }
    if not all(webhook_headers.values()):
        msg = "Missing Clerk webhook signature headers"
        raise AuthorizationError(msg)

    body = await request.body()

    try:
        event = Webhook(settings.clerk_webhook_secret).verify(body, webhook_headers)
    except WebhookVerificationError as exc:
        logger.warning("clerk_webhook_verification_failed", error=str(exc))
        msg = "Invalid Clerk webhook signature"
        raise AuthorizationError(msg) from exc

    payload = WebhookPayload.model_validate(event)
    user = await user_sync_service.sync_from_clerk_webhook(
        ClerkUserSyncPayload(
            event_type=payload.type,
            clerk_id=payload.data.id,
            email_addresses=[
                ClerkEmailAddress(
                    id=email.id,
                    email_address=email.email_address,
                )
                for email in payload.data.email_addresses
            ],
            primary_email_address_id=payload.data.primary_email_address_id,
            first_name=payload.data.first_name,
            last_name=payload.data.last_name,
            username=payload.data.username,
        ),
    )

    logger.info(
        "clerk_webhook_processed",
        clerk_id=payload.data.id,
        event_type=payload.type,
    )

    return WebhookSyncResponse(
        status="ignored" if user is None else "synced",
        event_type=payload.type,
        user=UserResponse.model_validate(user) if user else None,
    )
