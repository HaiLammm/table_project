from collections.abc import AsyncGenerator
from datetime import UTC, datetime, timedelta
from time import perf_counter
from uuid import uuid4

import pytest_asyncio
from sqlalchemy import insert, select
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession

from src.app.db.base import Base
from src.app.modules.auth.infrastructure.models import UserModel
from src.app.modules.srs.application.services import ReviewSchedulingService
from src.app.modules.srs.domain.value_objects import QueueMode, Rating
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


async def create_user(async_session: AsyncSession, clerk_id: str = "srs_user") -> UserModel:
    model = UserModel(clerk_id=clerk_id, email=f"{clerk_id}@example.com", display_name="SRS User")
    async_session.add(model)
    await async_session.commit()
    await async_session.refresh(model)
    return model


async def test_review_scheduling_service_persists_card_state_and_review_log(
    srs_schema: None,
    async_session: AsyncSession,
) -> None:
    user = await create_user(async_session)
    repository = SqlAlchemySrsCardRepository(async_session)
    service = ReviewSchedulingService(repository)

    created = await service.create_card_for_term(user_id=user.id, term_id=1001, language="en")
    outcome = await service.review_card(
        card_id=created.id or 0,
        user_id=user.id,
        rating=Rating.GOOD,
        response_time_ms=1250,
        session_id=uuid4(),
    )

    stored_card = await repository.get_card_by_id(created.id or 0, user.id)
    review_rows = await async_session.execute(select(SrsReviewModel))
    stored_review = review_rows.scalar_one()

    assert stored_card is not None
    assert stored_card.due_at == outcome.card.due_at
    assert stored_card.stability == outcome.card.stability
    assert stored_card.difficulty == outcome.card.difficulty
    assert stored_card.reps == 1
    assert stored_card.lapses == 0
    assert stored_card.fsrs_state["last_review"] is not None
    assert stored_review.card_id == created.id
    assert stored_review.user_id == user.id
    assert stored_review.rating == 3
    assert stored_review.response_time_ms == 1250


async def test_repository_lists_due_cards_in_overdue_due_new_order(
    srs_schema: None,
    async_session: AsyncSession,
) -> None:
    user = await create_user(async_session, clerk_id="srs_queue_user")
    repository = SqlAlchemySrsCardRepository(async_session)
    now = datetime.now(UTC)

    async_session.add_all(
        [
            SrsCardModel(
                user_id=user.id,
                term_id=1,
                language="en",
                due_at=now - timedelta(days=3),
                fsrs_state={"state": 2},
                reps=3,
            ),
            SrsCardModel(
                user_id=user.id,
                term_id=2,
                language="en",
                due_at=now - timedelta(hours=6),
                fsrs_state={"state": 2},
                reps=1,
            ),
            SrsCardModel(
                user_id=user.id,
                term_id=3,
                language="en",
                due_at=now - timedelta(days=7),
                fsrs_state={"state": 1},
                reps=0,
            ),
        ]
    )
    await async_session.commit()

    due_cards = await repository.list_due_cards(
        user_id=user.id,
        now=now,
        mode=QueueMode.FULL,
        limit=10,
        offset=0,
    )

    assert [card.term_id for card in due_cards.items] == [1, 2, 3]


async def test_repository_rejects_duplicate_cards_with_db_constraint(
    srs_schema: None,
    async_session: AsyncSession,
) -> None:
    user = await create_user(async_session, clerk_id="srs_duplicate_user")
    repository = SqlAlchemySrsCardRepository(async_session)
    service = ReviewSchedulingService(repository)

    await service.create_card_for_term(user_id=user.id, term_id=42, language="en")

    from src.app.modules.srs.domain.exceptions import DuplicateCardError

    try:
        await service.create_card_for_term(user_id=user.id, term_id=42, language="en")
    except DuplicateCardError:
        duplicate_detected = True
    else:
        duplicate_detected = False

    assert duplicate_detected is True


async def test_repository_computes_due_queue_under_hundred_milliseconds(
    srs_schema: None,
    async_session: AsyncSession,
) -> None:
    user = await create_user(async_session, clerk_id="srs_perf_user")
    now = datetime.now(UTC)
    rows = [
        {
            "user_id": user.id,
            "term_id": index + 1,
            "language": "en" if index % 2 == 0 else "jp",
            "due_at": now - timedelta(minutes=index + 1),
            "fsrs_state": {"state": 2, "card_id": index + 1},
            "stability": 2.0,
            "difficulty": 5.0,
            "reps": index % 5,
            "lapses": index % 2,
        }
        for index in range(10_000)
    ]
    await async_session.execute(insert(SrsCardModel), rows)
    await async_session.commit()

    repository = SqlAlchemySrsCardRepository(async_session)

    started_at = perf_counter()
    due_cards = await repository.list_due_cards(
        user_id=user.id,
        now=now,
        mode=QueueMode.FULL,
        limit=100,
        offset=0,
    )
    elapsed_seconds = perf_counter() - started_at

    assert due_cards.total_count == 10_000
    assert len(due_cards.items) == 100
    assert elapsed_seconds < 0.1
