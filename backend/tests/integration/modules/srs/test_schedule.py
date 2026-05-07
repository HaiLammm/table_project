from collections.abc import AsyncGenerator
from datetime import UTC, datetime, timedelta

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession

from src.app.db.base import Base
from src.app.modules.auth.infrastructure.models import UserModel
from src.app.modules.srs.infrastructure.models import SrsCardModel, SrsReviewModel
from src.app.modules.srs.infrastructure.repository import SqlAlchemySrsCardRepository


@pytest_asyncio.fixture
async def srs_schedule_schema(async_engine: AsyncEngine) -> AsyncGenerator[None, None]:
    assert UserModel.__table__ is not None
    assert SrsCardModel.__table__ is not None
    assert SrsReviewModel.__table__ is not None

    async with async_engine.begin() as connection:
        await connection.run_sync(Base.metadata.drop_all)
        await connection.run_sync(Base.metadata.create_all)

    yield

    async with async_engine.begin() as connection:
        await connection.run_sync(Base.metadata.drop_all)


async def create_user(async_session: AsyncSession, clerk_id: str = "schedule_user") -> UserModel:
    model = UserModel(
        clerk_id=clerk_id, email=f"{clerk_id}@example.com", display_name="Schedule User"
    )
    async_session.add(model)
    await async_session.commit()
    await async_session.refresh(model)
    return model


@pytest_asyncio.fixture
async def srs_schedule_schema(async_engine: AsyncEngine) -> AsyncGenerator[None, None]:
    async with async_engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)

    yield

    async with async_engine.begin() as connection:
        await connection.run_sync(Base.metadata.drop_all)


@pytest.mark.asyncio
async def test_schedule_endpoint_returns_today_tomorrow_this_week_buckets(
    srs_schedule_schema: None,
    async_session: AsyncSession,
) -> None:
    user = await create_user(async_session)
    repository = SqlAlchemySrsCardRepository(async_session)
    now = datetime.now(UTC)

    today_end = now.replace(hour=23, minute=59, second=59, microsecond=999999)
    tomorrow_end = today_end + timedelta(days=1)
    days_until_sunday = (6 - now.weekday()) % 7
    if days_until_sunday == 0 and now.weekday() == 6:
        week_end = today_end
    else:
        week_end = (now + timedelta(days=days_until_sunday)).replace(
            hour=23, minute=59, second=59, microsecond=999999
        )

    async_session.add_all(
        [
            SrsCardModel(
                user_id=user.id,
                term_id=1,
                language="en",
                due_at=now - timedelta(hours=2),
                fsrs_state={},
                reps=1,
            ),
            SrsCardModel(
                user_id=user.id,
                term_id=2,
                language="en",
                due_at=now - timedelta(hours=1),
                fsrs_state={},
                reps=2,
            ),
            SrsCardModel(
                user_id=user.id,
                term_id=3,
                language="en",
                due_at=tomorrow_end - timedelta(hours=1),
                fsrs_state={},
                reps=1,
            ),
            SrsCardModel(
                user_id=user.id,
                term_id=4,
                language="en",
                due_at=tomorrow_end + timedelta(days=1),
                fsrs_state={},
                reps=1,
            ),
            SrsCardModel(
                user_id=user.id,
                term_id=5,
                language="en",
                due_at=tomorrow_end + timedelta(days=3),
                fsrs_state={},
                reps=1,
            ),
        ]
    )
    await async_session.commit()

    schedule = await repository.count_due_cards_by_buckets(
        user.id, today_end, tomorrow_end, week_end
    )

    assert schedule.today.due_count == 2
    assert schedule.tomorrow.due_count == 1
    assert schedule.this_week.due_count == 2


@pytest.mark.asyncio
async def test_schedule_endpoint_returns_zeros_when_no_cards(
    srs_schedule_schema: None,
    async_session: AsyncSession,
) -> None:
    user = await create_user(async_session, clerk_id="empty_schedule_user")
    repository = SqlAlchemySrsCardRepository(async_session)
    now = datetime.now(UTC)

    today_end = now.replace(hour=23, minute=59, second=59, microsecond=999999)
    tomorrow_end = today_end + timedelta(days=1)
    days_until_sunday = (6 - now.weekday()) % 7
    if days_until_sunday == 0 and now.weekday() == 6:
        week_end = today_end
    else:
        week_end = (now + timedelta(days=days_until_sunday)).replace(
            hour=23, minute=59, second=59, microsecond=999999
        )

    schedule = await repository.count_due_cards_by_buckets(
        user.id, today_end, tomorrow_end, week_end
    )

    assert schedule.today.due_count == 0
    assert schedule.today.estimated_minutes == 0
    assert schedule.tomorrow.due_count == 0
    assert schedule.tomorrow.estimated_minutes == 0
    assert schedule.this_week.due_count == 0
    assert schedule.this_week.estimated_minutes == 0


@pytest.mark.asyncio
async def test_schedule_endpoint_with_review_history_uses_avg_response_time(
    srs_schedule_schema: None,
    async_session: AsyncSession,
) -> None:
    user = await create_user(async_session, clerk_id="schedule_with_reviews")
    repository = SqlAlchemySrsCardRepository(async_session)
    now = datetime.now(UTC)

    today_end = now.replace(hour=23, minute=59, second=59, microsecond=999999)
    tomorrow_end = today_end + timedelta(days=1)
    days_until_sunday = (6 - now.weekday()) % 7
    if days_until_sunday == 0 and now.weekday() == 6:
        week_end = today_end
    else:
        week_end = (now + timedelta(days=days_until_sunday)).replace(
            hour=23, minute=59, second=59, microsecond=999999
        )

    async_session.add_all(
        [
            SrsCardModel(
                user_id=user.id,
                term_id=10,
                language="en",
                due_at=now - timedelta(hours=2),
                fsrs_state={},
                reps=3,
            ),
            SrsReviewModel(
                user_id=user.id,
                card_id=1,
                rating=3,
                reviewed_at=now - timedelta(hours=1),
                response_time_ms=30000,
            ),
        ]
    )
    await async_session.commit()

    schedule = await repository.count_due_cards_by_buckets(
        user.id, today_end, tomorrow_end, week_end
    )

    assert schedule.today.due_count == 1
    assert schedule.today.estimated_minutes > 0
