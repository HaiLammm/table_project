import pytest
from unittest.mock import AsyncMock, MagicMock

from src.app.modules.enrichment.application.services import (
    CorpusOnlyEnrichmentService,
    GatewayEnrichmentService,
)
from src.app.modules.enrichment.domain.interfaces import EnrichedTerm


@pytest.fixture
def corpus_service():
    return CorpusOnlyEnrichmentService(session=None)


@pytest.mark.asyncio
async def test_corpus_only_service_returns_empty_list_when_no_session(corpus_service):
    result = await corpus_service.find_terms_for_request(
        topic="networking", language="en", level="B2", count=10
    )
    assert result == []


@pytest.mark.asyncio
async def test_gateway_service_returns_empty_list_when_no_session():
    service = GatewayEnrichmentService(session=None)
    result = await service.find_terms_for_request(
        topic="test", language="en", level="B2", count=10
    )
    assert result == []
