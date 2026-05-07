from collections.abc import AsyncGenerator
from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession

from src.app.db.base import Base
from src.app.modules.auth.infrastructure.models import UserModel
from src.app.modules.srs.application.services import ReviewSchedulingService
from src.app.modules.srs.domain.value_objects import Rating
from src.app.modules.srs.infrastructure.models import SrsCardModel, SrsReviewModel
from src.app.modules.srs.infrastructure.repository import SqlAlchemySrsCardRepository


@pytest_asyncio.fixture
async def srs_schema(async_engine: AsyncEngine) -> AsyncGenerator[None, None]:
    assert UserModel.__table__ is not None
    assert SrsCardModel.__table__ is not None
    assert SrsReviewModel.__table__ is not None

    async with async_engine.begin() as connection:
        await connection.run_sync(Base.metadata.drop_all)
        await connection.run_sync(Base.metadata.create_all)

    yield

    async with async_engine.begin() as connection:
        await connection.run_sync(Base.metadata.drop_all)


async def create_user(async_session: AsyncSession, clerk_id: str = "srs_stats_user") -> UserModel:
    model = UserModel(
        clerk_id=clerk_id, email=f"{clerk_id}@example.com", display_name="SRS Stats User"
    )
    async_session.add(model)
    await async_session.commit()
    await async_session.refresh(model)
    return model


async def test_session_stats_returns_counts_for_graduated_and_lapsed_cards(
    srs_schema: None,
    async_session: AsyncSession,
) -> None:
    user = await create_user(async_session)
    repository = SqlAlchemySrsCardRepository(async_session)
    service = ReviewSchedulingService(repository)

    session_id = uuid4()
    card1 = await service.create_card_for_term(user_id=user.id, term_id=1001, language="en")
    card2 = await service.create_card_for_term(user_id=user.id, term_id=1002, language="en")
    card3 = await service.create_card_for_term(user_id=user.id, term_id=1003, language="en")

    await service.review_card(
        card_id=card1.id or 0,
        user_id=user.id,
        rating=Rating.GOOD,
        session_id=session_id,
    )
    await service.review_card(
        card_id=card2.id or 0,
        user_id=user.id,
        rating=Rating.AGAIN,
        session_id=session_id,
    )
    await service.review_card(
        card_id=card3.id or 0,
        user_id=user.id,
        rating=Rating.EASY,
        session_id=session_id,
    )

    stats = await service.get_session_stats(user_id=user.id, session_id=session_id)

    assert stats.cards_reviewed == 3
    assert stats.cards_lapsed == 1
    assert stats.lapsed_card_ids == [card2.id]
    assert stats.tomorrow_due_count >= 0
    assert stats.tomorrow_estimated_minutes >= 0


async def test_session_stats_empty_session_returns_zeros(
    srs_schema: None,
    async_session: AsyncSession,
) -> None:
    user = await create_user(async_session)
    repository = SqlAlchemySrsCardRepository(async_session)
    service = ReviewSchedulingService(repository)

    session_id = uuid4()
    stats = await service.get_session_stats(user_id=user.id, session_id=session_id)

    assert stats.cards_reviewed == 0
    assert stats.cards_graduated == 0
    assert stats.cards_lapsed == 0
    assert stats.lapsed_card_ids == []
    assert stats.tomorrow_due_count == 0
    assert stats.tomorrow_estimated_minutes == 0


async def test_session_stats_graduation_threshold_boundary(
    srs_schema: None,
    async_session: AsyncSession,
) -> None:
    user = await create_user(async_session, clerk_id="srs_boundary_user")
    repository = SqlAlchemySrsCardRepository(async_session)
    service = ReviewSchedulingService(repository)

    session_id = uuid4()
    card = await service.create_card_for_term(user_id=user.id, term_id=2001, language="en")

    await service.review_card(
        card_id=card.id or 0,
        user_id=user.id,
        rating=Rating.EASY,
        session_id=session_id,
    )

    updated_card = await repository.get_card_by_id(card.id or 0, user.id)
    assert updated_card is not None

    stats = await service.get_session_stats(user_id=user.id, session_id=session_id)

    assert stats.cards_reviewed == 1
    if (
        updated_card.stability is not None
        and updated_card.stability >= 21.0
        and card.stability is not None
        and card.stability < 21.0
    ):
        assert stats.cards_graduated == 1
    else:
        assert stats.cards_graduated == 0


async def test_session_stats_response_matches_schema(
    srs_schema: None,
    async_session: AsyncSession,
) -> None:
    from src.app.modules.srs.api.schemas import SessionStatsResponse
    from src.app.modules.srs.domain.entities import SessionStats

    stats = SessionStats(
        cards_reviewed=3,
        cards_graduated=1,
        cards_lapsed=2,
        lapsed_card_ids=[10, 20],
        tomorrow_due_count=5,
        tomorrow_estimated_minutes=1,
    )

    response = SessionStatsResponse(
        cards_reviewed=stats.cards_reviewed,
        cards_graduated=stats.cards_graduated,
        cards_lapsed=stats.cards_lapsed,
        lapsed_card_ids=stats.lapsed_card_ids,
        tomorrow_due_count=stats.tomorrow_due_count,
        tomorrow_estimated_minutes=stats.tomorrow_estimated_minutes,
    )

    assert response.cards_reviewed == 3
    assert response.cards_graduated == 1
    assert response.cards_lapsed == 2
    assert response.lapsed_card_ids == [10, 20]
    assert response.tomorrow_due_count == 5
    assert response.tomorrow_estimated_minutes == 1


async def test_session_stats_tomorrow_due_count_against_db(
    srs_schema: None,
    async_session: AsyncSession,
) -> None:
    user = await create_user(async_session, clerk_id="srs_tmr_user")
    repository = SqlAlchemySrsCardRepository(async_session)
    service = ReviewSchedulingService(repository)

    _ = await service.create_card_for_term(user_id=user.id, term_id=5001, language="en")

    now = datetime.now(UTC)
    current_due_count = await repository.count_due_cards_for_date(user_id=user.id, date_end=now)
    assert current_due_count == 1

    tomorrow_end = (now + timedelta(days=1)).replace(
        hour=23,
        minute=59,
        second=59,
        microsecond=999999,
    )
    tomorrow_due_count = await repository.count_due_cards_for_date(
        user_id=user.id,
        date_end=tomorrow_end,
    )
    assert tomorrow_due_count >= 1
