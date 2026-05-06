from datetime import UTC, datetime

import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import insert
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker

from src.app.db.base import Base
from src.app.modules.vocabulary.infrastructure.models import (
    VocabularyDefinitionModel,
    VocabularyTermModel,
)


@pytest_asyncio.fixture
async def search_schema(async_engine: AsyncEngine):
    assert VocabularyTermModel.__table__ is not None
    assert VocabularyDefinitionModel.__table__ is not None

    async with async_engine.begin() as connection:
        await connection.run_sync(Base.metadata.drop_all)
        await connection.run_sync(Base.metadata.create_all)

    yield

    async with async_engine.begin() as connection:
        await connection.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture
async def search_client(
    search_schema,
    async_engine: AsyncEngine,
):
    from src.app.db.session import get_async_session
    from src.app.main import app

    session_factory = async_sessionmaker(
        bind=async_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    async def override_get_async_session():
        async with session_factory() as session:
            yield session

    app.dependency_overrides[get_async_session] = override_get_async_session

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as async_client:
        yield async_client

    app.dependency_overrides.clear()


async def test_search_endpoint_returns_pages_and_words(
    search_client: AsyncClient,
    async_engine: AsyncEngine,
) -> None:
    session_factory = async_sessionmaker(
        bind=async_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    async with session_factory() as session:
        await session.execute(
            insert(VocabularyTermModel).values(
                term="protocol",
                language="en",
                part_of_speech="noun",
                created_at=datetime.now(UTC),
            )
        )
        await session.execute(
            insert(VocabularyTermModel).values(
                term="network protocol",
                language="en",
                part_of_speech="noun",
                created_at=datetime.now(UTC),
            )
        )
        await session.commit()

    response = await search_client.get("/api/v1/search?query=protocol")

    assert response.status_code == 200
    data = response.json()
    assert data["collections"] == []
    assert data["pages"] == []
    assert len(data["words"]) == 2
    assert data["words"][0]["term"] == "protocol"


async def test_search_endpoint_matches_static_pages(
    search_client: AsyncClient,
) -> None:
    response = await search_client.get("/api/v1/search?query=settings")

    assert response.status_code == 200
    data = response.json()
    assert len(data["pages"]) == 1
    assert data["pages"][0]["href"] == "/settings"
