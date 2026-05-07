from collections.abc import AsyncGenerator
from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import insert, select
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker

from src.app.db.base import Base
from src.app.db.session import get_async_session
from src.app.main import app
from src.app.modules.auth.api.dependencies import get_current_user
from src.app.modules.auth.domain.entities import User
from src.app.modules.auth.domain.value_objects import UserTier
from src.app.modules.auth.infrastructure.models import UserModel
from src.app.modules.dashboard.infrastructure.models import (
    DiagnosticInsightModel,
    InsightSeenModel,
)
from src.app.modules.srs.infrastructure.models import SrsCardModel, SrsReviewModel
from src.app.modules.vocabulary.infrastructure.models import VocabularyTermModel


@pytest_asyncio.fixture
async def diagnostics_schema(async_engine: AsyncEngine) -> AsyncGenerator[None, None]:
    assert UserModel.__table__ is not None
    assert VocabularyTermModel.__table__ is not None
    assert SrsCardModel.__table__ is not None
    assert SrsReviewModel.__table__ is not None
    assert DiagnosticInsightModel.__table__ is not None
    assert InsightSeenModel.__table__ is not None

    async with async_engine.begin() as connection:
        await connection.run_sync(Base.metadata.drop_all)
        await connection.run_sync(Base.metadata.create_all)

    yield

    async with async_engine.begin() as connection:
        await connection.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture
async def diagnostics_client(
    diagnostics_schema: None,
    async_engine: AsyncEngine,
) -> AsyncGenerator[tuple[AsyncClient, User], None]:
    session_factory = async_sessionmaker(
        bind=async_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    async with session_factory() as session:
        user_model = UserModel(
            clerk_id="diagnostics_user",
            email="diagnostics@example.com",
            display_name="Diagnostics User",
        )
        session.add(user_model)
        await session.commit()
        await session.refresh(user_model)

    user = User(
        id=user_model.id,
        clerk_id=user_model.clerk_id,
        email=user_model.email,
        display_name=user_model.display_name,
        tier=UserTier.FREE,
    )

    async def override_get_async_session() -> AsyncGenerator[AsyncSession, None]:
        async with session_factory() as session:
            yield session

    async def override_get_current_user() -> User:
        return user

    app.dependency_overrides[get_async_session] = override_get_async_session
    app.dependency_overrides[get_current_user] = override_get_current_user

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as async_client:
        yield async_client, user

    app.dependency_overrides.clear()


async def test_diagnostics_flow_computes_fetches_and_marks_seen(
    diagnostics_client: tuple[AsyncClient, User],
    async_engine: AsyncEngine,
) -> None:
    client, user = diagnostics_client
    session_factory = async_sessionmaker(
        bind=async_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )
    now = datetime.now(UTC)

    async with session_factory() as session:
        await session.execute(
            insert(VocabularyTermModel),
            [
                {
                    "id": 1001,
                    "term": "protocol",
                    "language": "en",
                    "part_of_speech": "noun",
                    "created_at": now,
                },
                {
                    "id": 1002,
                    "term": "deploy",
                    "language": "en",
                    "part_of_speech": "verb",
                    "created_at": now,
                },
            ],
        )
        await session.execute(
            insert(SrsCardModel),
            [
                {
                    "id": 2001,
                    "user_id": user.id,
                    "term_id": 1001,
                    "language": "en",
                    "due_at": now - timedelta(days=1),
                    "fsrs_state": {"state": 2},
                    "reps": 4,
                    "lapses": 0,
                },
                {
                    "id": 2002,
                    "user_id": user.id,
                    "term_id": 1002,
                    "language": "en",
                    "due_at": now - timedelta(days=1),
                    "fsrs_state": {"state": 2},
                    "reps": 4,
                    "lapses": 2,
                },
            ],
        )

        reviews: list[dict[str, object]] = []
        for days_ago in range(16):
            review_day = now - timedelta(days=days_ago)
            reviews.append(
                {
                    "card_id": 2001,
                    "user_id": user.id,
                    "rating": 4,
                    "response_time_ms": 900,
                    "reviewed_at": review_day.replace(hour=8, minute=0, second=0, microsecond=0),
                    "session_id": uuid4(),
                }
            )
            reviews.append(
                {
                    "card_id": 2002,
                    "user_id": user.id,
                    "rating": 1,
                    "response_time_ms": 15000,
                    "reviewed_at": review_day.replace(hour=20, minute=0, second=0, microsecond=0),
                    "session_id": uuid4(),
                }
            )
            reviews.append(
                {
                    "card_id": 2001,
                    "user_id": user.id,
                    "rating": 3,
                    "response_time_ms": 1800,
                    "reviewed_at": review_day.replace(hour=13, minute=0, second=0, microsecond=0),
                    "session_id": uuid4(),
                }
            )

        await session.execute(insert(SrsReviewModel), reviews)
        await session.commit()

    session_id = str(uuid4())
    response = await client.get(f"/api/v1/diagnostics/insights?session_id={session_id}&limit=3")

    assert response.status_code == 200
    data = response.json()
    assert len(data["items"]) == 3
    assert {item["delivery_interval"] for item in data["items"]} == {5}
    assert any(item["action_href"] == "/dashboard" for item in data["items"])

    first_id = data["items"][0]["id"]
    seen_response = await client.post(
        f"/api/v1/diagnostics/insights/{first_id}/seen",
        json={"session_id": session_id},
    )
    assert seen_response.status_code == 200
    assert seen_response.json() == {"success": True}

    refreshed_response = await client.get(
        f"/api/v1/diagnostics/insights?session_id={session_id}&limit=3"
    )

    assert refreshed_response.status_code == 200
    refreshed_ids = {item["id"] for item in refreshed_response.json()["items"]}
    assert first_id not in refreshed_ids

    async with session_factory() as session:
        stored_insights = await session.execute(select(DiagnosticInsightModel))
        stored_seen = await session.execute(select(InsightSeenModel))
        assert len(stored_insights.scalars().all()) == 3
        assert len(stored_seen.scalars().all()) == 1
