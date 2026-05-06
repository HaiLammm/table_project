from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.app.db.session import get_async_session
from src.app.modules.vocabulary.application.services import VocabularyService
from src.app.modules.vocabulary.infrastructure.repository import VocabularyRepositoryImpl

SessionDependency = Annotated[AsyncSession, Depends(get_async_session)]


def get_vocabulary_service(session: SessionDependency) -> VocabularyService:
    repo = VocabularyRepositoryImpl(session)
    return VocabularyService(repo)


VocabularyServiceDependency = Annotated[VocabularyService, Depends(get_vocabulary_service)]
