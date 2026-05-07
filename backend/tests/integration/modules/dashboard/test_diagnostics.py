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
from src.app.modules.dashboard.infrastructure.repository import SqlAlchemyDiagnosticRepository
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
        for days_ago in range(15):
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
            reviews.append(
                {
                    "card_id": 2002,
                    "user_id": user.id,
                    "rating": 4,
                    "response_time_ms": 1700,
                    "reviewed_at": review_day.replace(hour=16, minute=0, second=0, microsecond=0),
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


async def test_diagnostic_repository_returns_extended_review_signal_fields(
    diagnostics_client: tuple[AsyncClient, User],
    async_engine: AsyncEngine,
) -> None:
    _client, user = diagnostics_client
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
                    "id": 3001,
                    "term": "protocol",
                    "language": "jp",
                    "part_of_speech": "noun",
                    "created_at": now,
                }
            ],
        )
        await session.execute(
            insert(SrsCardModel),
            [
                {
                    "id": 4001,
                    "user_id": user.id,
                    "term_id": 3001,
                    "language": "jp",
                    "due_at": now - timedelta(hours=1),
                    "fsrs_state": {"state": 2},
                    "reps": 3,
                    "lapses": 1,
                }
            ],
        )
        await session.execute(
            insert(SrsReviewModel),
            [
                {
                    "card_id": 4001,
                    "user_id": user.id,
                    "rating": 2,
                    "response_time_ms": 1800,
                    "reviewed_at": now,
                    "parallel_mode_active": True,
                    "session_length_s": 480,
                    "session_id": uuid4(),
                }
            ],
        )
        await session.commit()

    async with session_factory() as session:
        repository = SqlAlchemyDiagnosticRepository(session)
        rows = await repository.get_review_analytics(user.id or 0, days_back=30)

    assert len(rows) == 1
    assert rows[0]["language"] == "jp"
    assert rows[0]["parallel_mode_active"] is True
    assert rows[0]["term_id"] == 3001
    assert rows[0]["card_id"] == 4001


async def test_diagnostics_flow_persists_new_review_signal_columns_via_review_endpoint(
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
            insert(SrsCardModel),
            [
                {
                    "id": 5001,
                    "user_id": user.id,
                    "term_id": 9001,
                    "language": "en",
                    "due_at": now - timedelta(hours=1),
                    "fsrs_state": {
                        "state": 1,
                        "step": 0,
                        "due": (now - timedelta(hours=1)).isoformat(),
                    },
                    "reps": 0,
                    "lapses": 0,
                }
            ],
        )
        await session.commit()

    session_id = str(uuid4())
    response = await client.post(
        "/api/v1/srs_cards/5001/review",
        json={
            "rating": 3,
            "response_time_ms": 1400,
            "session_id": session_id,
            "session_length_s": 900,
            "parallel_mode_active": True,
        },
    )

    assert response.status_code == 200

    async with session_factory() as session:
        review_rows = await session.execute(select(SrsReviewModel))
        stored_review = review_rows.scalar_one()

    assert stored_review.session_length_s == 900
    assert stored_review.parallel_mode_active is True


async def test_diagnostics_flow_generates_time_category_and_cross_language_insights(
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
                    "id": 6001,
                    "term": "protocol",
                    "language": "jp",
                    "part_of_speech": "noun",
                    "created_at": now,
                },
                {
                    "id": 6002,
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
                    "id": 7001,
                    "user_id": user.id,
                    "term_id": 6001,
                    "language": "jp",
                    "due_at": now - timedelta(hours=1),
                    "fsrs_state": {"state": 2},
                    "reps": 4,
                    "lapses": 2,
                },
                {
                    "id": 7002,
                    "user_id": user.id,
                    "term_id": 6002,
                    "language": "en",
                    "due_at": now - timedelta(hours=1),
                    "fsrs_state": {"state": 2},
                    "reps": 4,
                    "lapses": 0,
                },
            ],
        )

        reviews: list[dict[str, object]] = []
        for days_ago in range(15):
            review_day = now - timedelta(days=days_ago)
            for offset in range(2):
                reviews.append(
                    {
                        "card_id": 7001,
                        "user_id": user.id,
                        "rating": 4,
                        "response_time_ms": 1200,
                        "session_length_s": 600,
                        "parallel_mode_active": False,
                        "reviewed_at": review_day.replace(
                            hour=8, minute=offset, second=0, microsecond=0
                        ),
                        "session_id": uuid4(),
                    }
                )
            for offset in range(2):
                reviews.append(
                    {
                        "card_id": 7001,
                        "user_id": user.id,
                        "rating": 1,
                        "response_time_ms": 1800,
                        "session_length_s": 600,
                        "parallel_mode_active": True,
                        "reviewed_at": review_day.replace(
                            hour=20, minute=offset, second=0, microsecond=0
                        ),
                        "session_id": uuid4(),
                    }
                )
            for offset in range(2):
                reviews.append(
                    {
                        "card_id": 7002,
                        "user_id": user.id,
                        "rating": 4,
                        "response_time_ms": 1600,
                        "session_length_s": 600,
                        "parallel_mode_active": False,
                        "reviewed_at": review_day.replace(
                            hour=13, minute=offset, second=0, microsecond=0
                        ),
                        "session_id": uuid4(),
                    }
                )

        await session.execute(insert(SrsReviewModel), reviews)
        await session.commit()

    session_id = str(uuid4())
    response = await client.get(f"/api/v1/diagnostics/insights?session_id={session_id}&limit=3")

    assert response.status_code == 200
    pattern_types = {item["type"] for item in response.json()["items"]}
    assert pattern_types == {
        "time_of_day_pattern",
        "category_specific_weakness",
        "cross_language_interference",
    }


async def test_diagnostics_flow_skips_insights_when_data_is_insufficient(
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
                    "id": 8001,
                    "term": "protocol",
                    "language": "en",
                    "part_of_speech": "noun",
                    "created_at": now,
                },
                {
                    "id": 8002,
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
                    "id": 8101,
                    "user_id": user.id,
                    "term_id": 8001,
                    "language": "en",
                    "due_at": now - timedelta(hours=1),
                    "fsrs_state": {"state": 2},
                    "reps": 2,
                    "lapses": 1,
                },
                {
                    "id": 8102,
                    "user_id": user.id,
                    "term_id": 8002,
                    "language": "en",
                    "due_at": now - timedelta(hours=1),
                    "fsrs_state": {"state": 2},
                    "reps": 2,
                    "lapses": 0,
                },
            ],
        )

        reviews: list[dict[str, object]] = []
        for days_ago in range(6):
            review_day = now - timedelta(days=days_ago)
            for offset in range(4):
                reviews.append(
                    {
                        "card_id": 8101 if offset % 2 == 0 else 8102,
                        "user_id": user.id,
                        "rating": 3,
                        "response_time_ms": 1200,
                        "parallel_mode_active": offset == 0,
                        "session_length_s": 500,
                        "reviewed_at": review_day.replace(
                            hour=9 + offset, minute=0, second=0, microsecond=0
                        ),
                        "session_id": uuid4(),
                    }
                )

        await session.execute(insert(SrsReviewModel), reviews)
        await session.commit()

    session_id = str(uuid4())
    response = await client.get(f"/api/v1/diagnostics/insights?session_id={session_id}&limit=3")

    assert response.status_code == 200
    assert response.json()["items"] == []
