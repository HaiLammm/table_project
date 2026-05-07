from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.app.db.session import get_async_session
from src.app.modules.auth.api.dependencies import get_current_user as get_authenticated_user
from src.app.modules.auth.domain.entities import User
from src.app.modules.collections.api.dependencies import get_collection_service
from src.app.modules.collections.application.services import CollectionService
from src.app.modules.srs.application.services import QueueStatsService, ReviewSchedulingService
from src.app.modules.srs.infrastructure.repository import SqlAlchemySrsCardRepository

SessionDependency = Annotated[AsyncSession, Depends(get_async_session)]
CurrentUserDependency = Annotated[User, Depends(get_authenticated_user)]


async def get_current_user(current_user: CurrentUserDependency) -> User:
    return current_user


def get_queue_stats_service(session: SessionDependency) -> QueueStatsService:
    return QueueStatsService(SqlAlchemySrsCardRepository(session))


def get_review_scheduling_service(
    session: SessionDependency,
    collection_service: Annotated[CollectionService, Depends(get_collection_service)],
) -> ReviewSchedulingService:
    return ReviewSchedulingService(
        SqlAlchemySrsCardRepository(session),
        collection_service=collection_service,
    )
