from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.app.db.session import get_async_session
from src.app.modules.auth.api.dependencies import get_current_user as get_authenticated_user
from src.app.modules.auth.domain.entities import User
from src.app.modules.collections.application.services import CollectionService
from src.app.modules.collections.infrastructure.repository import (
    SqlAlchemyCollectionRepository,
    SqlAlchemyCollectionTermRepository,
)
from src.app.modules.vocabulary.infrastructure.repository import VocabularyRepositoryImpl

SessionDependency = Annotated[AsyncSession, Depends(get_async_session)]
CurrentUserDependency = Annotated[User, Depends(get_authenticated_user)]


async def get_current_user(current_user: CurrentUserDependency) -> User:
    return current_user


def get_collection_service(session: SessionDependency) -> CollectionService:
    return CollectionService(
        SqlAlchemyCollectionRepository(session),
        SqlAlchemyCollectionTermRepository(session),
        VocabularyRepositoryImpl(session),
    )
