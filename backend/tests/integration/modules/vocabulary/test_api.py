from collections.abc import AsyncGenerator

import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import func, insert, select
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker

from src.app.db.base import Base
from src.app.modules.vocabulary.infrastructure.models import (
    VocabularyDefinitionModel,
    VocabularyTermModel,
)


@pytest_asyncio.fixture
async def vocabulary_schema(async_engine: AsyncEngine) -> AsyncGenerator[None, None]:
    assert VocabularyTermModel.__table__ is not None
    assert VocabularyDefinitionModel.__table__ is not None

    async with async_engine.begin() as connection:
        await connection.run_sync(Base.metadata.drop_all)
        await connection.run_sync(Base.metadata.create_all)

    yield

    async with async_engine.begin() as connection:
        await connection.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture
async def vocabulary_client(
    vocabulary_schema: None,
    async_engine: AsyncEngine,
) -> AsyncGenerator[AsyncClient, None]:
    from src.app.db.session import get_async_session
    from src.app.main import app

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


async def test_list_vocabulary_terms_empty(
    vocabulary_client: AsyncClient,
) -> None:
    response = await vocabulary_client.get("/api/v1/vocabulary_terms")

    assert response.status_code == 200
    data = response.json()
    assert data["items"] == []
    assert data["total"] == 0
    assert data["page"] == 1
    assert data["page_size"] == 20
    assert data["has_next"] is False


async def test_list_vocabulary_terms_with_pagination(
    vocabulary_client: AsyncClient,
    async_engine: AsyncEngine,
) -> None:
    from datetime import UTC, datetime

    session_factory = async_sessionmaker(
        bind=async_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    async with session_factory() as session:
        for i in range(25):
            await session.execute(
                insert(VocabularyTermModel).values(
                    term=f"term_{i}",
                    language="en",
                    cefr_level="B1",
                    part_of_speech="noun",
                    created_at=datetime.now(UTC),
                )
            )
        await session.commit()

        count_result = await session.execute(select(func.count(VocabularyTermModel.id)))
        total = count_result.scalar_one()
        assert total == 25

    response = await vocabulary_client.get("/api/v1/vocabulary_terms?page=1&page_size=10")

    assert response.status_code == 200
    data = response.json()
    assert len(data["items"]) == 10
    assert data["total"] == 25
    assert data["page"] == 1
    assert data["page_size"] == 10
    assert data["has_next"] is True


async def test_list_vocabulary_terms_with_cefr_filter(
    vocabulary_client: AsyncClient,
    async_engine: AsyncEngine,
) -> None:
    from datetime import UTC, datetime

    session_factory = async_sessionmaker(
        bind=async_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    async with session_factory() as session:
        for i, level in enumerate(["A1", "B1", "B1", "C1"]):
            await session.execute(
                insert(VocabularyTermModel).values(
                    term=f"term_{i}",
                    language="en",
                    cefr_level=level,
                    part_of_speech="noun",
                    created_at=datetime.now(UTC),
                )
            )
        await session.commit()

    response = await vocabulary_client.get("/api/v1/vocabulary_terms?cefr_level=B1")

    assert response.status_code == 200
    data = response.json()
    for item in data["items"]:
        assert item["cefr_level"] == "B1"


async def test_list_vocabulary_terms_with_jlpt_filter(
    vocabulary_client: AsyncClient,
    async_engine: AsyncEngine,
) -> None:
    from datetime import UTC, datetime

    session_factory = async_sessionmaker(
        bind=async_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    async with session_factory() as session:
        for i, level in enumerate(["N5", "N2", "N2", "N1"]):
            await session.execute(
                insert(VocabularyTermModel).values(
                    term=f"term_{i}",
                    language="jp",
                    jlpt_level=level,
                    part_of_speech="noun",
                    created_at=datetime.now(UTC),
                )
            )
        await session.commit()

    response = await vocabulary_client.get("/api/v1/vocabulary_terms?jlpt_level=N2")

    assert response.status_code == 200
    data = response.json()
    for item in data["items"]:
        assert item["jlpt_level"] == "N2"


async def test_search_vocabulary_terms(
    vocabulary_client: AsyncClient,
    async_engine: AsyncEngine,
) -> None:
    from datetime import UTC, datetime

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
        await session.commit()

    response = await vocabulary_client.get("/api/v1/vocabulary_terms/search?query=protocol")

    assert response.status_code == 200
    data = response.json()
    assert len(data["items"]) == 1
    assert data["items"][0]["term"] == "protocol"


async def test_get_vocabulary_term_by_id(
    vocabulary_client: AsyncClient,
    async_engine: AsyncEngine,
) -> None:
    from datetime import UTC, datetime

    session_factory = async_sessionmaker(
        bind=async_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    async with session_factory() as session:
        model = VocabularyTermModel(
            term="test_term",
            language="en",
            part_of_speech="noun",
            created_at=datetime.now(UTC),
        )
        session.add(model)
        await session.commit()
        await session.refresh(model)
        term_id = model.id

        def_model = VocabularyDefinitionModel(
            term_id=term_id,
            language="en",
            definition="A test definition",
            source="seed",
        )
        session.add(def_model)
        await session.commit()

    response = await vocabulary_client.get(f"/api/v1/vocabulary_terms/{term_id}")

    assert response.status_code == 200
    data = response.json()
    assert data["term"] == "test_term"
    assert len(data["definitions"]) == 1


async def test_get_vocabulary_term_not_found(
    vocabulary_client: AsyncClient,
) -> None:
    response = await vocabulary_client.get("/api/v1/vocabulary_terms/99999")

    assert response.status_code == 404
    data = response.json()
    assert data["error"]["code"] == "TERM_NOT_FOUND"


async def test_get_vocabulary_term_children(
    vocabulary_client: AsyncClient,
    async_engine: AsyncEngine,
) -> None:
    from datetime import UTC, datetime

    session_factory = async_sessionmaker(
        bind=async_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    async with session_factory() as session:
        parent = VocabularyTermModel(
            term="Parent",
            language="en",
            part_of_speech="noun",
            created_at=datetime.now(UTC),
        )
        session.add(parent)
        await session.commit()
        await session.refresh(parent)

        child1 = VocabularyTermModel(
            term="Child1",
            language="en",
            parent_id=parent.id,
            part_of_speech="noun",
            created_at=datetime.now(UTC),
        )
        child2 = VocabularyTermModel(
            term="Child2",
            language="en",
            parent_id=parent.id,
            part_of_speech="noun",
            created_at=datetime.now(UTC),
        )
        session.add(child1)
        session.add(child2)
        await session.commit()

    response = await vocabulary_client.get(f"/api/v1/vocabulary_terms/{parent.id}/children")

    assert response.status_code == 200
    data = response.json()
    assert len(data["items"]) == 2
    assert {item["term"] for item in data["items"]} == {"Child1", "Child2"}
