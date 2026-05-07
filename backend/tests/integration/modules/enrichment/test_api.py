from collections.abc import AsyncGenerator

import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker

from src.app.db.base import Base
from src.app.db.session import get_async_session
from src.app.main import app
from src.app.modules.vocabulary.infrastructure.models import (
    VocabularyDefinitionModel,
    VocabularyTermModel,
)


@pytest_asyncio.fixture
async def enrichment_schema(async_engine: AsyncEngine) -> AsyncGenerator[None, None]:
    async with async_engine.begin() as connection:
        await connection.run_sync(Base.metadata.drop_all)
        await connection.run_sync(Base.metadata.create_all)

    yield

    async with async_engine.begin() as connection:
        await connection.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture
async def enrichment_client(
    enrichment_schema: None,
    async_engine: AsyncEngine,
) -> AsyncGenerator[AsyncClient, None]:
    session_factory = async_sessionmaker(
        bind=async_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    async def override_get_async_session() -> AsyncGenerator[AsyncSession, None]:
        async with session_factory() as session:
            yield session

    app.dependency_overrides[get_async_session] = override_get_async_session

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as async_client:
        yield async_client

    app.dependency_overrides.clear()


async def test_preview_vocabulary_request_empty(
    enrichment_client: AsyncClient,
) -> None:
    response = await enrichment_client.post(
        "/api/v1/vocabulary_requests/preview",
        json={
            "topic": "networking",
            "language": "en",
            "level": "B2",
            "count": 10,
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert data["terms"] == []
    assert data["corpus_match_count"] == 0
    assert data["gap_count"] == 10
    assert data["requested_count"] == 10


async def test_preview_vocabulary_request_with_corpus_matches(
    enrichment_client: AsyncClient,
    async_engine: AsyncEngine,
) -> None:
    from datetime import UTC, datetime

    session_factory = async_sessionmaker(
        bind=async_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    async with session_factory() as session:
        term = VocabularyTermModel(
            term="protocol",
            language="en",
            cefr_level="B2",
            part_of_speech="noun",
            created_at=datetime.now(UTC),
        )
        session.add(term)
        await session.commit()
        await session.refresh(term)

        definition = VocabularyDefinitionModel(
            term_id=term.id,
            language="en",
            definition="A set of rules",
            source="corpus",
        )
        session.add(definition)
        await session.commit()

    response = await enrichment_client.post(
        "/api/v1/vocabulary_requests/preview",
        json={
            "topic": "protocol",
            "language": "en",
            "level": "B2",
            "count": 10,
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert data["corpus_match_count"] == 1
    assert data["gap_count"] == 9
    assert len(data["terms"]) == 1
    assert data["terms"][0]["term"] == "protocol"
    assert data["terms"][0]["source"] == "corpus"


async def test_preview_vocabulary_request_validation_error(
    enrichment_client: AsyncClient,
) -> None:
    response = await enrichment_client.post(
        "/api/v1/vocabulary_requests/preview",
        json={
            "topic": "",
            "language": "en",
            "level": "B2",
            "count": 10,
        },
    )

    assert response.status_code == 422


async def test_preview_vocabulary_request_invalid_count(
    enrichment_client: AsyncClient,
) -> None:
    response = await enrichment_client.post(
        "/api/v1/vocabulary_requests/preview",
        json={
            "topic": "networking",
            "language": "en",
            "level": "B2",
            "count": 100,
        },
    )

    assert response.status_code == 422


async def test_confirm_vocabulary_request_empty(
    enrichment_client: AsyncClient,
) -> None:
    response = await enrichment_client.post(
        "/api/v1/vocabulary_requests/confirm",
        json={"term_ids": [99999]},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["added_count"] == 0
    assert data["skipped_count"] == 0


async def test_confirm_vocabulary_request_creates_terms(
    enrichment_client: AsyncClient,
    async_engine: AsyncEngine,
) -> None:
    from datetime import UTC, datetime

    session_factory = async_sessionmaker(
        bind=async_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    term_id = None
    async with session_factory() as session:
        term = VocabularyTermModel(
            term="confirm_test",
            language="en",
            cefr_level="B1",
            part_of_speech="noun",
            created_at=datetime.now(UTC),
        )
        session.add(term)
        await session.commit()
        await session.refresh(term)
        term_id = term.id

        definition = VocabularyDefinitionModel(
            term_id=term_id,
            language="en",
            definition="Test definition",
            source="corpus",
        )
        session.add(definition)
        await session.commit()

    response = await enrichment_client.post(
        "/api/v1/vocabulary_requests/confirm",
        json={"term_ids": [term_id]},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["added_count"] == 1
    assert data["skipped_count"] == 0


async def test_confirm_vocabulary_request_dedup(
    enrichment_client: AsyncClient,
    async_engine: AsyncEngine,
) -> None:
    from datetime import UTC, datetime

    session_factory = async_sessionmaker(
        bind=async_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    term_id = None
    async with session_factory() as session:
        term = VocabularyTermModel(
            term="dedup_test",
            language="en",
            cefr_level="B1",
            part_of_speech="noun",
            created_at=datetime.now(UTC),
        )
        session.add(term)
        await session.commit()
        await session.refresh(term)
        term_id = term.id

        definition = VocabularyDefinitionModel(
            term_id=term_id,
            language="en",
            definition="Test definition",
            source="corpus",
        )
        session.add(definition)
        await session.commit()

    response1 = await enrichment_client.post(
        "/api/v1/vocabulary_requests/confirm",
        json={"term_ids": [term_id]},
    )
    assert response1.status_code == 200
    assert response1.json()["added_count"] == 1

    response2 = await enrichment_client.post(
        "/api/v1/vocabulary_requests/confirm",
        json={"term_ids": [term_id]},
    )
    assert response2.status_code == 200
    assert response2.json()["added_count"] == 0
    assert response2.json()["skipped_count"] == 1
