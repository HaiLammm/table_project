from collections.abc import AsyncGenerator

import pytest_asyncio
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession

from src.app.db.base import Base
from src.app.modules.auth.infrastructure.models import UserModel
from src.app.modules.srs.application.services import ReviewSchedulingService
from src.app.modules.srs.domain.exceptions import NoReviewToUndoError
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


async def create_user(async_session: AsyncSession, clerk_id: str = "srs_undo_user") -> UserModel:
    model = UserModel(
        clerk_id=clerk_id, email=f"{clerk_id}@example.com", display_name="SRS Undo User"
    )
    async_session.add(model)
    await async_session.commit()
    await async_session.refresh(model)
    return model


async def test_full_undo_flow_restores_card_state_in_database(
    srs_schema: None,
    async_session: AsyncSession,
) -> None:
    user = await create_user(async_session)
    repository = SqlAlchemySrsCardRepository(async_session)
    service = ReviewSchedulingService(repository)

    created = await service.create_card_for_term(user_id=user.id, term_id=1001, language="en")
    original_due_at = created.due_at

    await service.review_card(
        card_id=created.id or 0,
        user_id=user.id,
        rating=Rating.GOOD,
        response_time_ms=1200,
    )

    undo_result = await service.undo_last_review(card_id=created.id or 0, user_id=user.id)

    stored_card = await repository.get_card_by_id(created.id or 0, user.id)
    assert stored_card is not None
    assert stored_card.due_at == original_due_at
    assert stored_card.reps == 0
    assert stored_card.lapses == 0

    review_rows = await async_session.execute(
        select(SrsReviewModel).where(SrsReviewModel.card_id == created.id)
    )
    stored_reviews = review_rows.scalars().all()
    assert len(stored_reviews) == 0


async def test_undo_with_no_review_returns_error(
    srs_schema: None,
    async_session: AsyncSession,
) -> None:
    user = await create_user(async_session, clerk_id="srs_undo_no_review")
    repository = SqlAlchemySrsCardRepository(async_session)
    service = ReviewSchedulingService(repository)

    created = await service.create_card_for_term(user_id=user.id, term_id=2001, language="en")

    try:
        await service.undo_last_review(card_id=created.id or 0, user_id=user.id)
    except NoReviewToUndoError:
        error_raised = True
    else:
        error_raised = False

    assert error_raised is True


async def test_undo_preserves_previous_state_columns_in_review_before_deletion(
    srs_schema: None,
    async_session: AsyncSession,
) -> None:
    user = await create_user(async_session, clerk_id="srs_undo_preserve")
    repository = SqlAlchemySrsCardRepository(async_session)
    service = ReviewSchedulingService(repository)

    created = await service.create_card_for_term(user_id=user.id, term_id=3001, language="en")

    await service.review_card(
        card_id=created.id or 0,
        user_id=user.id,
        rating=Rating.GOOD,
        response_time_ms=900,
    )

    review_rows = await async_session.execute(
        select(SrsReviewModel)
        .where(
            SrsReviewModel.card_id == created.id,
            SrsReviewModel.user_id == user.id,
        )
        .order_by(SrsReviewModel.reviewed_at.desc())
        .limit(1)
    )
    review_before_undo = review_rows.scalar_one_or_none()
    assert review_before_undo is not None
    assert review_before_undo.previous_fsrs_state is not None
    assert review_before_undo.previous_stability is None
    assert review_before_undo.previous_difficulty is None
    assert review_before_undo.previous_reps == 0
    assert review_before_undo.previous_lapses == 0
