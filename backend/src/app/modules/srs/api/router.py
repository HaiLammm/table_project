from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status

from src.app.modules.auth.domain.exceptions import AuthenticationError
from src.app.modules.srs.api.dependencies import (
    CurrentUserDependency,
    get_queue_stats_service,
    get_review_scheduling_service,
)
from src.app.modules.srs.api.schemas import (
    CreateCardsForCollectionRequest,
    CreateCardsForCollectionResponse,
    CreateSrsCardRequest,
    CreateSrsCardResponse,
    DueCardResponse,
    DueCardsResponse,
    EmbeddedTermResponse,
    QueueStatsResponse,
    ReviewCardRequest,
    ReviewCardResponse,
    SessionStatsResponse,
    UndoReviewResponse,
    UpcomingScheduleResponse,
)
from src.app.modules.srs.application.services import QueueStatsService, ReviewSchedulingService
from src.app.modules.srs.domain.value_objects import QueueMode, Rating

router = APIRouter()

QueueStatsServiceDependency = Annotated[QueueStatsService, Depends(get_queue_stats_service)]
ReviewSchedulingServiceDependency = Annotated[
    ReviewSchedulingService,
    Depends(get_review_scheduling_service),
]
type QueueModeQuery = Annotated[QueueMode, Query()]
type QueueLimitQuery = Annotated[int, Query(ge=1, le=100)]
type QueueOffsetQuery = Annotated[int, Query(ge=0)]


def _require_user_id(current_user: CurrentUserDependency) -> int:
    if current_user.id is None:
        msg = "Current user is missing an internal id"
        raise AuthenticationError(msg)

    return current_user.id


@router.post(
    "/cards",
    status_code=status.HTTP_201_CREATED,
    response_model=CreateSrsCardResponse,
    tags=["srs_cards"],
)
async def create_srs_card(
    payload: CreateSrsCardRequest,
    current_user: CurrentUserDependency,
    review_scheduling_service: ReviewSchedulingServiceDependency,
) -> CreateSrsCardResponse:
    card = await review_scheduling_service.create_card_for_term(
        user_id=_require_user_id(current_user),
        term_id=payload.term_id,
        language=payload.language,
    )
    return CreateSrsCardResponse.model_validate(card)


@router.post(
    "/cards/create-for-collection",
    status_code=status.HTTP_201_CREATED,
    response_model=CreateCardsForCollectionResponse,
    tags=["srs_cards"],
)
async def create_cards_for_collection(
    payload: CreateCardsForCollectionRequest,
    current_user: CurrentUserDependency,
    review_scheduling_service: ReviewSchedulingServiceDependency,
) -> CreateCardsForCollectionResponse:
    created_count, skipped_count = await review_scheduling_service.create_cards_for_collection(
        user_id=_require_user_id(current_user),
        collection_id=payload.collection_id,
        language=payload.language,
    )
    return CreateCardsForCollectionResponse(
        created_count=created_count,
        skipped_count=skipped_count,
    )


@router.get("/queue-stats", response_model=QueueStatsResponse, tags=["srs_cards"])
async def read_queue_stats(
    current_user: CurrentUserDependency,
    queue_stats_service: QueueStatsServiceDependency,
    collection_id: int | None = Query(None),
) -> QueueStatsResponse:
    queue_stats = await queue_stats_service.get_queue_stats(
        _require_user_id(current_user), collection_id=collection_id
    )
    return QueueStatsResponse.model_validate(queue_stats)


@router.get("/queue", response_model=DueCardsResponse, tags=["srs_cards"])
async def read_due_queue(
    current_user: CurrentUserDependency,
    queue_stats_service: QueueStatsServiceDependency,
    mode: QueueModeQuery = QueueMode.FULL,
    limit: QueueLimitQuery = 100,
    offset: QueueOffsetQuery = 0,
    collection_id: int | None = Query(None),
) -> DueCardsResponse:
    due_cards = await queue_stats_service.get_due_cards(
        user_id=_require_user_id(current_user),
        mode=mode,
        limit=limit,
        offset=offset,
        collection_id=collection_id,
    )
    items: list[DueCardResponse] = []
    for item in due_cards.items:
        if item.card.id is None:
            continue
        card_resp = DueCardResponse.model_validate(item.card)
        if item.term is not None:
            card_resp.term = EmbeddedTermResponse(
                id=item.term.id,
                term=item.term.term,
                language=item.term.language,
                cefr_level=item.term.cefr_level,
                jlpt_level=item.term.jlpt_level,
                part_of_speech=item.term.part_of_speech,
                definitions=item.term.definitions,
            )
        items.append(card_resp)
    return DueCardsResponse(
        items=items,
        total_count=due_cards.total_count,
        limit=due_cards.limit,
        offset=due_cards.offset,
        mode=due_cards.mode,
    )


@router.get("/due", response_model=DueCardsResponse, tags=["srs_cards"])
async def read_due_cards(
    current_user: CurrentUserDependency,
    queue_stats_service: QueueStatsServiceDependency,
    mode: QueueModeQuery = QueueMode.FULL,
    limit: QueueLimitQuery = 100,
    offset: QueueOffsetQuery = 0,
) -> DueCardsResponse:
    return await read_due_queue(
        current_user=current_user,
        queue_stats_service=queue_stats_service,
        mode=mode,
        limit=limit,
        offset=offset,
    )


@router.get("/session-stats", response_model=SessionStatsResponse, tags=["srs_cards"])
async def read_session_stats(
    session_id: UUID,
    current_user: CurrentUserDependency,
    review_scheduling_service: ReviewSchedulingServiceDependency,
) -> SessionStatsResponse:
    stats = await review_scheduling_service.get_session_stats(
        user_id=_require_user_id(current_user),
        session_id=session_id,
    )
    return SessionStatsResponse.model_validate(stats)


@router.post("/{card_id}/review", response_model=ReviewCardResponse, tags=["srs_cards"])
async def review_srs_card(
    card_id: int,
    payload: ReviewCardRequest,
    current_user: CurrentUserDependency,
    review_scheduling_service: ReviewSchedulingServiceDependency,
) -> ReviewCardResponse:
    review_result = await review_scheduling_service.review_card(
        card_id=card_id,
        user_id=_require_user_id(current_user),
        rating=Rating.from_score(payload.rating),
        response_time_ms=payload.response_time_ms,
        session_length_s=payload.session_length_s,
        parallel_mode_active=payload.parallel_mode_active,
        session_id=payload.session_id,
    )
    card_payload = CreateSrsCardResponse.model_validate(review_result.card).model_dump()
    return ReviewCardResponse(
        **card_payload,
        next_due_at=review_result.next_due_at,
        interval_display=review_result.interval_display,
    )


@router.post("/{card_id}/review/undo", response_model=UndoReviewResponse, tags=["srs_cards"])
async def undo_srs_review(
    card_id: int,
    current_user: CurrentUserDependency,
    review_scheduling_service: ReviewSchedulingServiceDependency,
) -> UndoReviewResponse:
    review_result = await review_scheduling_service.undo_last_review(
        card_id=card_id,
        user_id=_require_user_id(current_user),
    )
    card_payload = CreateSrsCardResponse.model_validate(review_result.card).model_dump()
    return UndoReviewResponse(
        **card_payload,
        next_due_at=review_result.next_due_at,
        interval_display=review_result.interval_display,
        stability=review_result.card.stability,
        difficulty=review_result.card.difficulty,
        reps=review_result.card.reps,
        lapses=review_result.card.lapses,
    )


@router.get("/schedule", response_model=UpcomingScheduleResponse, tags=["srs_cards"])
async def read_upcoming_schedule(
    current_user: CurrentUserDependency,
    queue_stats_service: QueueStatsServiceDependency,
) -> UpcomingScheduleResponse:
    schedule = await queue_stats_service.get_upcoming_schedule(_require_user_id(current_user))
    return UpcomingScheduleResponse.model_validate(schedule)
