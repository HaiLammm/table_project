from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.app.db.session import get_async_session
from src.app.modules.enrichment.application.services import CorpusOnlyEnrichmentService
from src.app.modules.enrichment.domain.interfaces import EnrichmentServiceInterface

SessionDependency = Annotated[AsyncSession, Depends(get_async_session)]


def get_enrichment_service(session: SessionDependency) -> EnrichmentServiceInterface:
    return CorpusOnlyEnrichmentService(session)


EnrichmentServiceDependency = Annotated[
    "EnrichmentServiceInterface", Depends(get_enrichment_service)
]
