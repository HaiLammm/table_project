from collections.abc import AsyncGenerator
from typing import Annotated

import structlog
from arq import create_pool
from arq.connections import ArqRedis, RedisSettings
from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response, status
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession
from svix.webhooks import Webhook, WebhookVerificationError

from src.app.core.config import settings
from src.app.core.exceptions import build_error_payload
from src.app.db.session import get_async_session
from src.app.modules.auth.api.dependencies import get_current_user as get_authenticated_user
from src.app.modules.auth.api.schemas import (
    AccountDeletionRequest,
    DataExportResponse,
    DataExportStatusResponse,
    UserPreferencesResponse,
    UserPreferencesUpdateRequest,
    UserResponse,
    WebhookPayload,
    WebhookSyncResponse,
)
from src.app.modules.auth.application.services import (
    AccountDeletionService,
    ClerkEmailAddress,
    ClerkUserSyncPayload,
    DataExportService,
    UserPreferencesService,
    UserPreferencesUpdateInput,
    UserSyncService,
)
from src.app.modules.auth.domain.entities import User
from src.app.modules.auth.domain.exceptions import (
    AuthenticationError,
    AuthorizationError,
    UserNotFoundError,
)
from src.app.modules.auth.infrastructure.repository import SqlAlchemyUserRepository

logger = structlog.get_logger().bind(module="auth_api")
router = APIRouter()
SessionDependency = Annotated[AsyncSession, Depends(get_async_session)]


def get_user_sync_service(
    session: SessionDependency,
) -> UserSyncService:
    return UserSyncService(SqlAlchemyUserRepository(session))


def get_user_preferences_service(
    session: SessionDependency,
) -> UserPreferencesService:
    return UserPreferencesService(SqlAlchemyUserRepository(session))


def get_data_export_service(
    session: SessionDependency,
) -> DataExportService:
    repository = SqlAlchemyUserRepository(session)
    return DataExportService(repository, repository, repository)


def get_account_deletion_service(
    session: SessionDependency,
) -> AccountDeletionService:
    repository = SqlAlchemyUserRepository(session)
    return AccountDeletionService(repository, repository, repository)


async def get_arq_pool() -> AsyncGenerator[ArqRedis, None]:
    pool = await create_pool(RedisSettings.from_dsn(settings.redis_url))
    try:
        yield pool
    finally:
        await pool.aclose(close_connection_pool=True)


CurrentUserDependency = Annotated[User, Depends(get_authenticated_user)]
UserSyncServiceDependency = Annotated[UserSyncService, Depends(get_user_sync_service)]
UserPreferencesServiceDependency = Annotated[
    UserPreferencesService,
    Depends(get_user_preferences_service),
]
DataExportServiceDependency = Annotated[DataExportService, Depends(get_data_export_service)]
AccountDeletionServiceDependency = Annotated[
    AccountDeletionService,
    Depends(get_account_deletion_service),
]
ArqDependency = Annotated[ArqRedis, Depends(get_arq_pool)]


def _require_user_id(current_user: User) -> int:
    if current_user.id is None:
        msg = "User not found"
        raise UserNotFoundError(msg)

    return current_user.id


@router.get("/users/me", response_model=UserResponse, tags=["users"])
async def read_current_user(
    current_user: CurrentUserDependency,
) -> UserResponse:
    return UserResponse.model_validate(current_user)


@router.get("/users/me/preferences", response_model=UserPreferencesResponse, tags=["users"])
async def read_current_user_preferences(
    current_user: CurrentUserDependency,
    user_preferences_service: UserPreferencesServiceDependency,
) -> UserPreferencesResponse:
    preferences = await user_preferences_service.get_preferences(
        user_id=_require_user_id(current_user),
    )
    return UserPreferencesResponse.model_validate(preferences)


@router.put("/users/me/preferences", response_model=UserPreferencesResponse, tags=["users"])
async def update_current_user_preferences(
    payload: UserPreferencesUpdateRequest,
    current_user: CurrentUserDependency,
    user_preferences_service: UserPreferencesServiceDependency,
) -> UserPreferencesResponse:
    preferences = await user_preferences_service.update_preferences(
        user_id=_require_user_id(current_user),
        updates=UserPreferencesUpdateInput(
            learning_goal=payload.learning_goal,
            english_level=payload.english_level,
            japanese_level=payload.japanese_level,
            daily_study_minutes=payload.daily_study_minutes,
            it_domain=payload.it_domain,
            notification_email=payload.notification_email,
            notification_review_reminder=payload.notification_review_reminder,
        ),
    )
    return UserPreferencesResponse.model_validate(preferences)


@router.post("/users/me/data-export", response_model=DataExportResponse, tags=["users"])
async def request_current_user_data_export(
    current_user: CurrentUserDependency,
    data_export_service: DataExportServiceDependency,
    arq_pool: ArqDependency,
) -> DataExportResponse:
    data_export = await data_export_service.request_export(_require_user_id(current_user))
    if data_export.id is None:
        msg = "Data export was not created"
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=build_error_payload("data_export_create_failed", msg),
        )

    await arq_pool.enqueue_job("process_data_export", data_export.id)

    return DataExportResponse(
        export_id=data_export.id,
        status=data_export.status,
        created_at=data_export.created_at,
    )


@router.get(
    "/users/me/data-export/{export_id}",
    response_model=DataExportStatusResponse,
    tags=["users"],
    name="read_current_user_data_export_status",
)
async def read_current_user_data_export_status(
    export_id: int,
    request: Request,
    current_user: CurrentUserDependency,
    data_export_service: DataExportServiceDependency,
    download: bool = Query(default=False),
) -> DataExportStatusResponse | FileResponse:
    data_export = await data_export_service.get_export_for_user(
        user_id=_require_user_id(current_user),
        export_id=export_id,
    )

    if download:
        if data_export.status != "ready" or data_export.file_path is None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=build_error_payload(
                    "data_export_not_ready",
                    "Data export is not ready for download",
                ),
            )

        return FileResponse(
            path=data_export.file_path,
            media_type="application/zip",
            filename=f"data-export-{data_export.id}.zip",
        )

    download_url = None
    if data_export.status == "ready" and data_export.file_path is not None:
        status_url = request.url_for(
            "read_current_user_data_export_status",
            export_id=str(export_id),
        )
        download_url = f"{status_url}?download=true"

    return DataExportStatusResponse(
        export_id=data_export.id or export_id,
        status=data_export.status,
        created_at=data_export.created_at,
        expires_at=data_export.expires_at,
        download_url=download_url,
    )


@router.delete(
    "/users/me",
    status_code=status.HTTP_204_NO_CONTENT,
    tags=["users"],
)
async def delete_current_user_account(
    payload: AccountDeletionRequest,
    current_user: CurrentUserDependency,
    account_deletion_service: AccountDeletionServiceDependency,
) -> Response:
    await account_deletion_service.delete_account(current_user, payload.confirmation_email)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


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
