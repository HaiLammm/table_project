from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.app.db.session import get_async_session
from src.app.modules.auth.api.dependencies import get_current_user as get_authenticated_user
from src.app.modules.auth.domain.entities import User
from src.app.modules.dashboard.application.services import DiagnosticsService
from src.app.modules.dashboard.infrastructure.repository import SqlAlchemyDiagnosticRepository

SessionDependency = Annotated[AsyncSession, Depends(get_async_session)]
CurrentUserDependency = Annotated[User, Depends(get_authenticated_user)]


async def get_current_user(current_user: CurrentUserDependency) -> User:
    return current_user


def get_diagnostics_service(session: SessionDependency) -> DiagnosticsService:
    return DiagnosticsService(SqlAlchemyDiagnosticRepository(session))
